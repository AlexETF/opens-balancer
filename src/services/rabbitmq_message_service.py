import json
import os
import operator
from time import time
import logging
from config import config
from novaclient.v2 import Client
from services.migrate_service import MigrateService
from threading import Lock, Timer
from services.filters import core_filter, ram_filter, disk_filter

class RabbitMQMessageService(object):

    def __init__(self, auth_service, logger = None):
        self.__compute_nodes = {}
        self.__vm_instances = {}
        self.__services = {}
        self.__auth_service = auth_service
        self.__migrate_service = MigrateService(auth_service = auth_service, logger = logger)

        #   Filters used for filtering hosts
        self.__filters = {'ram'  : ram_filter.RamFilter(),
                          'vcpu' : core_filter.CoreFilter(),
                          'disk' : disk_filter.DiskFilter()
                         }

        #   Variable that indicates if this service needs to check for overload
        self.__check_overload = False
        self.__task = None
        self.__lock = Lock()
        # Logger object
        self.logger = logger or logging.getLogger(__name__)

    def stop_periodic_check(self):
        if self.__task != None:
            self.logger.info('Periodic collectiong of data canceled')
            self.__task.cancel()
            self.__task = None

    def start_periodic_check(self):
        self.stop_periodic_check()
        self.__task = Timer(config.periodic_check_interval * 60, self.__periodic_check)
        self.__task.setDaemon(True)
        self.__task.start()
        self.logger.info('Scheduled periodic check for %d min' % config.periodic_check_interval)

    def initialize(self):
        self.__lock.acquire()
        print os.linesep
        self.logger.info('Initializing RabbitMQMessageService')
        client = Client(session=self.__auth_service.get_session())
        self.logger.info('Collecting information about compute nodes')
        hypervisors  = client.hypervisors.list(detailed=True)
        self.logger.info('Collecting information about services')
        services = client.services.list()
        self.logger.info('Collecting information about VMs')
        servers  = client.servers.list(detailed=True)
        self.logger.info('Processing collected data')

        init_services = {}
        init_compute_nodes = {}
        init_vm_instances = {}

        for service in services:
            service_node = Service()
            service_node.id = service.id
            service_node.binary = service.binary
            service_node.created_at = service.updated_at
            service_node.disabled = service.status
            service_node.host = service.host
            service_node.topic = service.binary

            init_services[service_node.id] = service_node

        for hypervisor in hypervisors:
            node = ComputeNode()
            node.id = hypervisor.id
            node.free_disk_gb = hypervisor.free_disk_gb
            node.free_ram_mb = hypervisor.free_ram_mb
            node.host_ip = hypervisor.host_ip
            node.hypervisor_hostname = hypervisor.hypervisor_hostname
            node.hypervisor_type = hypervisor.hypervisor_type
            node.local_gb = hypervisor.local_gb
            node.local_gb_used = hypervisor.local_gb_used
            node.memory_mb = hypervisor.memory_mb
            node.memory_mb_used = hypervisor.memory_mb_used
            node.running_vms = hypervisor.running_vms
            node.service_id = hypervisor.service['id']
            node.host = hypervisor.service['host']
            node.vcpus = hypervisor.vcpus
            node.vcpus_used = hypervisor.vcpus_used

            node.state = hypervisor.state
            node.status = hypervisor.status

            self.__calculate_node_overload_and_weight(node)
            init_compute_nodes[node.id] = node

        for server in servers:
            server = server.to_dict()
            vm_id = server['id']
            if vm_id in self.__vm_instances.keys():
                vm_instance = self.__vm_instances[vm_id]
                vm_instance.hostname = server['name']
                vm_instance.availability_zone = server['OS-EXT-AZ:availability_zone']
                vm_instance.new_task_state = server['OS-EXT-STS:task_state']
                vm_instance.state = server['OS-EXT-STS:vm_state']
                vm_instance.host = server['OS-EXT-SRV-ATTR:host']
                vm_instance.hostname = server['name']
            else:
                vm_instance = VMInstance()
                vm_instance.id = vm_id
                vm_instance.availability_zone = server['OS-EXT-AZ:availability_zone']
                vm_instance.created_at = server['OS-SRV-USG:launched_at']
                vm_instance.display_name = server['name']
                vm_instance.host = server['OS-EXT-SRV-ATTR:host']
                vm_instance.hostname = server['name']
                vm_instance.new_task_state = server['OS-EXT-STS:task_state']
                vm_instance.state = server['OS-EXT-STS:vm_state']
                vm_instance.tenant_id = server['tenant_id']
                vm_instance.user_id = server['user_id']

                vm_instance.instance_flavor_id = server['flavor']['id']
                flavor = client.flavors.get(flavor = vm_instance.instance_flavor_id)
                flavor = flavor.to_dict()
                vm_instance.instance_flavor = flavor['name']
                vm_instance.disk_gb = flavor['disk']
                vm_instance.ephemeral_gb = flavor['OS-FLV-EXT-DATA:ephemeral']
                vm_instance.vcpus = flavor['vcpus']
                vm_instance.memory_mb = flavor['ram']

                image_meta = client.images.get(image = server['image']['id'])
                image_meta = image_meta.to_dict()
                vm_instance.image_meta.min_disk = image_meta['minDisk']
                vm_instance.image_meta.min_ram = image_meta['minRam']

            init_vm_instances[vm_instance.id] = vm_instance

        self.__services = init_services
        self.__compute_nodes = init_compute_nodes
        self.__vm_instances = init_vm_instances
        for instance in self.__vm_instances.values():
            self.__process_vm_instance(vm_instance = instance)
        self.__check_overload = True

        self.__lock.release()


    def parse_message(self, routing_key, message):
        self.__lock.acquire()
        #remove wrapper oslo.message in json
        message = json.loads(message)
        while 'oslo.message' in message:
            message = json.loads(message['oslo.message'])
        #print json.dumps(message, indent=4, sort_keys=4, separators=(',', ': '))
        if routing_key == 'conductor':
            self.__parse_conductor_message(message)
        elif routing_key == 'notifications.info':
            self.__parse_notification_info_message(message)

        self.__lock.release()

    def find_service_by_host(self, host):
        for service in self.__services.values():
            if service.host == host:
                return service
        return None

    def find_node_by_service_id(self, service_id):
        for node in self.__compute_nodes.values():
            if node.service_id == service_id:
                return node
        return None

    def find_node_by_hostname(self, hostname):
        for node in self.__compute_nodes.values():
            if node.hypervisor_hostname == hostname:
                return node
        return None

    def add_vm_instance_to_node(self, vm_instance):
        service = self.find_service_by_host(vm_instance.host)
        if service is not None:
            node = self.find_node_by_service_id(service.id)
            if node is not None:
                vm_instance.compute_node = node
                node.vm_instances[vm_instance.id] = vm_instance
                return True
        return False

    def check_overload(self):
        self.__lock.acquire()
        if self.__check_overload == False or len(self.__compute_nodes) == 0:
            self.__lock.release()
            return
        else:
            self.logger.debug('Sorting hosts overload')
            hosts = self.__get_hosts_ordered()
            node = None
            self.logger.debug('Searching for the most overloaded host')
            for host in hosts:
                if host.is_free_to_migrate_instances():
                    node = host
                    self.logger.debug('Found host %s' % (host.hypervisor_hostname))
                    break
                self.logger.debug('Skipping host %s , it has migrating instances' % host.hypervisor_hostname)
            if node == None:
                self.logger.info('Not available host')
                self.__check_overload = False
                self.__lock.release()
                return
            hosts.sort(key = operator.attrgetter('metrics_weight'))
            for vm in node.vm_instances.values():
                mig_time = vm.last_migrate_time
                if vm.is_ready_for_migrating() and (mig_time == None or ((time() - mig_time) > config.migrate_time * 60)):
                    self.logger.debug('Found instance to migrate %s' % vm.display_name)
                    for available_node in hosts:
                        if available_node.id == node.id:
                            self.logger.info('Reached the same host, exit')
                            break
                        passes = True
                        weight_with = 0
                        weight_without = 0
                        for filt in self.__filters.values():
                            passes = passes and filt.filter_one(host = available_node, vm = vm)
                            weight_with += filt.weight_host_with_vm(host = available_node, vm = vm)
                            weight_without += filt.weight_host_without_vm(host = node, vm = vm)
                        if passes and weight_without >= weight_with:
                            self.logger.info('Weight with: %r Weight without: %r' % (weight_with, weight_without))
                            if self.__migrate_service.schedule_migrate(vm.id, node):
                                self.logger.debug('Scheduled migrate')
                            else:
                                self.logger.debug('Failed to schedule migrate')
                            self.__check_overload = False
                            self.__lock.release()
                            return
                        if not passes:
                            self.logger.debug("Host %s doesn't have enough resources " % available_node.hypervisor_hostname)
                        if not weight_without >= weight_with:
                            self.logger.debug('Migration will have no effect')
            self.__check_overload = False
            self.__lock.release()


    def __get_hosts_ordered(self):
        if len(self.__compute_nodes) < 2:
            return []
        hosts = []
        for node in self.__compute_nodes.values():
            if node.is_running() and node.are_data_synced():
                hosts.append(node)
        hosts.sort(key = operator.attrgetter('metrics_weight'), reverse = True)
        return hosts

    @property
    def migrate_service(self):
        return self.__migrate_service

    @migrate_service.setter
    def migrate_service(self, service):
        self.__migrate_service = service

    @property
    def compute_nodes_list(self):
        return self.__compute_nodes.values()

    @property
    def vm_instances_list(self):
        return self.__vm_instances.values()

    @property
    def services_list(self):
        return self.__services.values()

    def print_all_info(self):
        for node in self.__compute_nodes.values():
            node.print_info()

        for vm_instance in self.__vm_instances.values():
            vm_instance.print_info()
            vm_instance.image_meta.print_info()

        for service in self.__services.values():
            service.print_info()

    def print_short_info(self):
        # print('Total compute nodes: %d' % len(self.__compute_nodes))
        # print('Total services: %d' % len(self.__services))
        self.logger.info('Total vms: %d' % len(self.__vm_instances))
        for node in self.__compute_nodes.values():
            self.logger.info('Node %s: %d State: %s, %s' % (node.hypervisor_hostname, len(node.vm_instances), node.state, node.status))

    def __calculate_node_overload_and_weight(self, node):
        weight = 0
        overloaded = False
        for filt in self.__filters.values():
            weight += filt.weight_host(host = node)
            overloaded = overloaded or filt.overloaded(host = node)
        node.metrics_weight = weight
        node.overloaded = overloaded

    def __parse_conductor_message(self, message):
        parsed_json = message
        method = parsed_json['method']
        if method == 'compute_node_update':
            node_id = parsed_json['args']['node']['id']
            if node_id in self.__compute_nodes.keys():
                node = self.__compute_nodes[node_id]
            else:
                node = ComputeNode()
            node.project_name = parsed_json.get('_context_project_name', '')
            node.id = node_id
            values = parsed_json.get('args',{}).get('values',{})
            node.created_at = values.get('created_at', '')
            node.free_disk_gb = values.get('free_disk_gb', -1)
            node.free_ram_mb = values.get('free_ram_mb', -1)
            node.host_ip = values.get('host_ip', '')
            node.hypervisor_hostname = values.get('hypervisor_hostname', '')
            node.hypervisor_type = values.get('hypervisor_type', '')
            node.local_gb = values.get('local_gb', -1)
            node.local_gb_used = values.get('local_gb_used', -1)
            node.memory_mb = values.get('memory_mb', -1)
            node.memory_mb_used = values.get('memory_mb_used', -1)
            node.running_vms = values.get('running_vms', -1)
            node.service_id = values.get('service_id', node.service_id)
            node.vcpus = values.get('vcpus', -1)
            node.vcpus_used = values.get('vcpus_used', -1)

            self.__calculate_node_overload_and_weight(node = node)
            self.__compute_nodes[node.id] = node

            self.__check_overload = True

            node.print_info()

        elif method == 'service_update':
            parsed_json = message
            service_dict = parsed_json.get('args', {}).get('service', {})
            service_id = service_dict['id']
            if service_id in self.__services.keys():
                service_obj = self.__services[service_id]
            else:
                service_obj = Service()
            service_obj.id = service_id
            service_obj.binary = service_dict['binary']
            service_obj.created_at = service_dict['created_at']
            service_obj.disabled = service_dict['disabled']
            service_obj.host = service_dict['host']
            service_obj.topic = service_dict['topic']

            self.__services[service_id] = service_obj

    def __parse_notification_info_message(self, message):
        parsed_json = message
        event_type = parsed_json['event_type']
        if event_type == 'compute.instance.update':
            payload = parsed_json['payload']
            vm_id = payload['instance_id']
            if vm_id in self.__vm_instances.keys():
                vm_instance = self.__vm_instances[vm_id]
            else:
                vm_instance = VMInstance()

            vm_instance.project_name = parsed_json['_context_project_name']
            vm_instance.id = vm_id
            vm_instance.availability_zone = payload.get('availability_zone', '')
            vm_instance.created_at = payload.get('created_at', '')
            vm_instance.disk_gb = payload.get('disk_gb', -1)
            vm_instance.display_name = payload.get('display_name', -1)
            vm_instance.ephemeral_gb = payload.get('ephemeral_gb', -1)
            vm_instance.host = payload.get('host', '')
            vm_instance.hostname = payload.get('hostname', '')
            vm_instance.vcpus = payload.get('vcpus', -1)
            vm_instance.instance_flavor = payload.get('instance_type', '')
            vm_instance.instance_flavor_id = payload.get('instance_flavor_id', -1)

            image_meta = payload.get('image_meta', {})
            vm_instance.image_meta.base_image_ref = image_meta.get('base_image_ref', '')
            vm_instance.image_meta.container_format = image_meta.get('container_format', '')
            vm_instance.image_meta.disk_format = image_meta.get('disk_format', '')
            vm_instance.image_meta.min_disk = image_meta.get('min_disk', -1)
            vm_instance.image_meta.min_ram = image_meta.get('min_ram', -1)

            vm_instance.hypervisor_hostname = payload.get('node', '')
            vm_instance.memory_mb = payload.get('memory_mb', -1)
            vm_instance.os_type = payload.get('os_type', -1)
            vm_instance.state = payload.get('state', '')
            vm_instance.old_state = payload.get('old_state', '')
            vm_instance.new_task_state = payload.get('new_task_state', '')
            vm_instance.old_task_state = payload.get('old_task_state', '')
            vm_instance.tenant_id = payload.get('tenant_id', -1)
            vm_instance.user_id = payload.get('user_id', -1)

            self.__vm_instances[vm_id] = vm_instance

            self.__process_vm_instance(vm_instance)

            # vm_instance.print_info()

    def __process_vm_instance(self, vm_instance):
        self.logger.debug('Instance %s State: %s' % (vm_instance.display_name, vm_instance.state))
        
        if vm_instance.is_building():
            if vm_instance.compute_node is not None:
                vm_instance.compute_node.remove_from_vm_instances(vm_instance.id)
            self.add_vm_instance_to_node(vm_instance)

        elif vm_instance.needs_to_verify_migrate():
            self.__migrate_service.schedule_confirm(vm_instance.id)
            if vm_instance.compute_node is not None:
                vm_instance.compute_node.remove_from_vm_instances(vm_instance.id)
            self.add_vm_instance_to_node(vm_instance)

        elif vm_instance.is_active():
            if vm_instance.is_verified_migrate():
                vm_instance.last_migrate_time = time()
                self.__migrate_service.confirm_task_done(vm_instance.id)

            if vm_instance.compute_node is not None:
                vm_instance.compute_node.remove_from_vm_instances(vm_instance.id)
            self.add_vm_instance_to_node(vm_instance)

        elif vm_instance.is_deleted():
            if vm_instance.id in self.__vm_instances.keys():
                del self.__vm_instances[vm_instance.id]
                if vm_instance.compute_node is not None:
                    vm_instance.compute_node.remove_from_vm_instances(vm_instance.id)

        elif vm_instance.is_in_error_state():
            self.logger.info('Instance %s is in error state' % (vm_instance.display_name))
            if vm_instance.compute_node is not None:
                vm_instance.compute_node.remove_from_vm_instances(vm_instance.id)
            self.add_vm_instance_to_node(vm_instance)
        else:
            if vm_instance.compute_node is not None:
                vm_instance.compute_node.remove_from_vm_instances(vm_instance.id)
            self.add_vm_instance_to_node(vm_instance)

    def __periodic_check(self):
        self.initialize()
        self.__task = Timer(config.periodic_check_interval * 60, self.__periodic_check)
        self.__task.setDaemon(True)
        self.__task.start()
        print os.linesep
        self.logger.info('Scheduled periodic check for %d min' % config.periodic_check_interval)

#
#   Class that holds system information about servers running
#   nova-compute service in OpenStack cloud
#
class ComputeNode(object):

    def __init__(self):
        self.id = None
        self.project_name = None
        self.created_at = None
        self.free_disk_gb = None
        self.free_ram_mb = None
        self.host_ip = None
        self.host = None
        self.hypervisor_hostname = None
        self.hypervisor_type = None
        self.local_gb = None
        self.local_gb_used = None
        self.memory_mb = None
        self.memory_mb_used = None
        self.running_vms = None
        self.service_id = None
        self.vcpus = None
        self.vcpus_used = None

        self.vm_instances = {}

        self.state = None   #up and down
        self.status = None  #enabled and disabled

        self.overloaded = None
        self.metrics_weight = None

    def are_data_synced(self):
        if len(self.vm_instances) == self.running_vms:
            return True
        return False

    def is_running(self):
        if self.state == 'up' and self.status == 'enabled':
            return True
        return False

    def remove_from_vm_instances(self, vm_id):
        instance = None
        if vm_id in self.vm_instances.keys():
            instance = self.vm_instances[vm_id]
            del self.vm_instances[vm_id]
            instance.compute_node = None
        return instance

    def is_free_to_migrate_instances(self):
        for vm in self.vm_instances.values():
            if vm.is_migrating():
                return False
        return True

    def num_migrating_instances(self):
        num = 0
        for vm in self.vm_instances.values():
            if vm.is_migrating():
                num += 1
        return num

    def print_info(self):
        print os.linesep
        print('----------------------------------------------------------------------------')
        print('ID: %r   Project name: %r    Created at: %s' % (self.id, self.project_name, self.created_at))
        print('Host IP: %s  Service ID: %r' % (self.host_ip, self.service_id))
        print('Hypervisor Hostname: %s  Type: %s' % (self.hypervisor_hostname, self.hypervisor_type))
        print('Local disk(GB): %r  Local disk used(GB): %r    Free Disk(GB): %r' % (self.local_gb, self.local_gb_used, self.free_disk_gb))
        print('Total RAM(MB): %r  RAM used(MB): %r    Free RAM(MB): %r' % (self.memory_mb, self.memory_mb_used, self.free_ram_mb))
        print('Total VCPU-s: %r VCPU-s used: %r' % (self.vcpus, self.vcpus_used))
        print('Number of Running VM-s: %r' % (self.running_vms))
        print('----------------------------------------------------------------------------')



class Service(object):

    def __init__(self):
        self.id = -1
        self.binary = ''
        self.created_at = ''
        self.disabled = ''
        self.host = ''
        self.topic = ''

    def print_info(self):
        print('----------------------- Service info --------------------------')
        print('ID: %r   Created at: %s' % (self.id, self.created_at))
        print('Host: %s     Disabled: %s' % (self.host, self.disabled))
        print('Binary: %s   Topic: %s' % (self.binary, self.topic))
        print('--------------------------------------------------------------')

#
#   Class that holds information of VM running on compute node
#
class VMInstance(object):

    def __init__(self):
        self.id = -1
        self.created_at = ''
        self.availability_zone = ''
        self.display_name = ''
        self.disk_gb = -1
        self.ephemeral_gb = -1
        self.vcpus = ''
        self.host = ''
        self.hostname = ''
        self.image_meta = ImageMeta()
        self.instance_flavor = ''
        self.instance_flavor_id = -1
        self.hypervisor_hostname = ''
        self.memory_mb = -1
        self.os_type = ''

        self.state = None
        self.old_state = None
        self.old_task_state = None
        self.new_task_state = None

        self.tenant_id = ''
        self.user_id = ''

        self.compute_node = None
        self.last_migrate_time = None
    #
    #   Method that will check if vm instance is overloaded
    #   If overload is detected vm needs to be migrated to another
    #   compute node
    #
    def check_for_overload(self):
        print('TO DO: Not yet implemented !')

    def is_active(self):
        if self.state == 'active':
            return True

    def is_building(self):
        states = ['scheduling', 'networking', 'block_device_mapping', 'spawning']
        if self.state == 'building':
            return True
        elif self.new_task_state in states:
            return True
        else:
            return False

    def is_migrating(self):
        states = ['resize_prep', 'resize_migrating', 'resize_migrated', 'resize_finish', 'migrating']
        if self.state == 'resized':
            return True
        elif self.new_task_state in states:
            return True
        else:
            return False

    def needs_to_verify_migrate(self):
        if self.state == 'resized' and self.new_task_state == None:
            return True
        return False

    def is_verified_migrate(self):
        if self.state == 'active' and self.old_state == 'resized':
            return True
        return False

    def is_in_error_state(self):
        if  self.state == 'error':
            return True
        return False

    def is_deleted(self):
        if self.state == 'deleted':
            return True
        return False

    def is_ready_for_migrating(self):
        if self.is_active() and self.new_task_state == None:
            return True
        return False

    def print_info(self):
        print('     *******************************************************************************')
        print('     Instance ID: %r     Created At: %s' % (self.id, self.created_at))
        print('     Display name: %r    Availability Zone: %s' % (self.display_name, self.availability_zone))
        print('     Tenant ID: %s' % self.tenant_id)
        print('     User ID: %s' % self.user_id)
        print('     Host: %s    Hostname: %s' % (self.host, self.hostname))
        print('     Flavor: %s  Flavor ID: %r' % (self.instance_flavor, self.instance_flavor_id))
        print('     Hypervisor Node: %s    OS Type: %s' % (self.hypervisor_hostname, self.os_type))
        print('     Disk(GB): %r    Ephemeral disk(GB): %r  RAM Memory(MB): %r' % (self.disk_gb, self.ephemeral_gb, self.memory_mb))
        print('     Current state: %s   Old state: %s' % (self.state, self.old_state))
        print('     New task state: %s  Old task state: %s' % (self.new_task_state, self.old_task_state))
        print('     *******************************************************************************')



class ImageMeta(object):

    def __init__(self):
        self.base_image_ref = ''
        self.container_format = ''
        self.disk_format = ''
        self.min_disk = -1
        self.min_ram = -1

    def print_info(self):
        print('         ````````````````````````` Image info ````````````````````````````')
        print('         Base image ref: %s' % (self.base_image_ref))
        print('         Container format: %s    Disk format: %s' % (self.container_format, self.disk_format))
        print('         Min disk(GB): %r    Min RAM(MB): %r' % (self.min_disk, self.min_ram))
        print('         `````````````````````````````````````````````````````````````````')
