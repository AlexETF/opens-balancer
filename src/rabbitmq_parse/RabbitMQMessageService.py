
import sys
import json
import os
from novaclient.v2 import Client
from nova_migrate import MigrateService
from threading import Lock

class RabbitMQMessageService(object):

    def __init__(self, auth_service):
        self.__compute_nodes = {}
        self.__vm_instances = {}
        self.__services = {}
        self.__auth_service = auth_service
        self.__migrate_service = MigrateService(auth_service)
        #   Variable that indicates if this service needs to check for overload
        self.__things_changed = False

    def initialize(self):
        print("INFO: Initializing RabbitMQMessageService")
        client = Client(session=self.__auth_service.get_session())
        hypervisors  = client.hypervisors.list(detailed=True)
        print('INFO: Collecting information about services')
        services = client.services.list()
        for service in services:
            service_node = Service()
            service_node.id = service.id
            service_node.binary = service.binary
            service_node.created_at = service.updated_at
            service_node.disabled = service.status
            service_node.host = service.host
            service_node.topic = service.binary

            self.__services[service_node.id] = service_node

        print("INFO: Collecting information about compute nodes")
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

            self.__compute_nodes[node.id] = node

        print("INFO: Collecting information about VMs")
        servers  = client.servers.list(detailed=True)
        for server in servers:
            server = server.to_dict()
            vm_instance = VMInstance()
            vm_instance.id = server['id']
            vm_instance.availability_zone = server['OS-EXT-AZ:availability_zone']
            vm_instance.created_at = server['OS-SRV-USG:launched_at']
            vm_instance.display_name = server['name']
            vm_instance.host = server['OS-EXT-SRV-ATTR:host']
            vm_instance.hostname = server['name']
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

            self.__vm_instances[vm_instance.id] = vm_instance

            status = server['status']
            self.__process_nova_vm_status(vm_instance = vm_instance, status = status)

        self.__things_changed = True


    def parse_message(self, routing_key, message):
        #remove wrapper oslo.message in json
        message = json.loads(message)
        while 'oslo.message' in message:
            message = json.loads(message['oslo.message'])
        #print json.dumps(message, indent=4, sort_keys=4, separators=(',', ': '))
        if routing_key == 'conductor':
            self.__parse_conductor_message(message)
        elif routing_key == 'notifications.info':
            self.__parse_notification_info_message(message)
        else:
            print('ERROR: Unsupported parsing of message with routing key %s' % routing_key)
        return


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

    def add_vm_active_to_node(self, vm_instance):
        service = self.find_service_by_host(vm_instance.host)
        if service is not None:
            node = self.find_node_by_service_id(service.id)
            if node is not None:
                vm_instance.compute_node = node
                node.vm_active[vm_instance.id] = vm_instance
                return True
        return False

    def add_vm_migrating_to_node(self, vm_instance):
        service = self.find_service_by_host(vm_instance.host)
        if service is not None:
            node = self.find_node_by_service_id(service.id)
            if node is not None:
                vm_instance.compute_node = node
                node.vm_migrating[vm_instance.id] = vm_instance
                return True
        return False

    def check_overload(self):
        if self.__things_changed == False or len(self.__compute_nodes) == 0:
            return
        else:
            nodes = self.find_min_max_instance_nodes()
            self.__things_changed == False
            if nodes is not None:
                minimum = nodes[0]
                maximum = nodes[1]
                if minimum.id == maximum.id:
                    self.__things_changed == False
                    return
                if (len(maximum.vm_active) - len(minimum.vm_active)) < 2:
                    self.__things_changed == False
                    return
                for instance in maximum.vm_active.values():
                    scheduled = self.migrate_service.schedule_migrate(instance.id, maximum)
                    if scheduled == True:
                        maximum.remove_from_vm_active(instance.id)
                        maximum.vm_migrating[instance.id] = instance
                        break
                self.__things_changed == False


    def find_min_max_instance_nodes(self):
        if len(self.__compute_nodes) == 0:
            return None
        maximum = self.__compute_nodes[self.__compute_nodes.keys()[0]]
        minimum = maximum
        for node in self.__compute_nodes.values():
            if maximum.running_vms < node.running_vms:
                maximum = node
            if minimum.running_vms > node.running_vms:
                minimum = node
        return (minimum, maximum)


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
        # print('Total number of compute nodes: %d' % len(self.__compute_nodes))
        # print('Total number of services: %d' % len(self.__services))
        print('Total number of vms: %d' % len(self.__vm_instances))
        for node in self.__compute_nodes.values():
            print('Number of active vms on node %s: %d In migrate process: %d' % (node.hypervisor_hostname, len(node.vm_active), len(node.vm_migrating)))

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

            self.__compute_nodes[node.id] = node

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

        else:
            print('ERROR: Unsupproted parsing of conductor message with method %s' % parsed_json['method'])
            return

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

            self.__process_rabbitmq_vm_state(vm_instance)

            vm_instance.print_info()

        else:
            print('ERROR: Unsupproted parsing of conductor message with event %s' % parsed_json['event_type'])
            return

    def __process_nova_vm_status(self, vm_instance, status):
        if status == 'ACTIVE':
            self.add_vm_active_to_node(vm_instance)
        elif status == 'MIGRATING' or status == 'RESIZING':
            self.add_vm_migrating_to_node(vm_instance)
        elif status == 'VERIFY_RESIZE':
            self.__migrate_service.schedule_confirm(vm_instance.id)

    def __process_rabbitmq_vm_state(self, vm_instance):
        if vm_instance.state == 'active':

            if vm_instance.new_task_state == None:
                if vm_instance.old_task_state == 'resize_finish':
                    self.__migrate_service.schedule_confirm(vm_instance.id)
                elif vm_instance.old_task_state == 'migrating':
                    if vm_instance.compute_node is not None:
                        vm_instance.compute_node.remove_from_vm_migrating(vm_instance.id)
                    self.add_vm_active_to_node(vm_instance)
                    self.__things_changed = True
                else:
                    if vm_instance.compute_node is not None:
                        vm_instance.compute_node.remove_from_vm_active(vm_instance.id)
                        vm_instance.compute_node.remove_from_vm_migrating(vm_instance.id)
                    self.add_vm_active_to_node(vm_instance)
                    self.__things_changed = True

            elif vm_instance.new_task_state == 'resize_migrating' and vm_instance.old_task_state == 'resize_prep':
                if vm_instance.compute_node is not None:
                    vm_instance.compute_node.remove_from_vm_active(vm_instance.id)
                    vm_instance.compute_node.vm_migrating[vm_instance.id] = vm_instance
                    self.__things_changed = True

            elif vm_instance.new_task_state == 'migrating' and vm_instance.old_task_state == 'migrating':
                if vm_instance.compute_node is not None:
                    vm_instance.compute_node.remove_from_vm_active(vm_instance.id)
                    vm_instance.compute_node.vm_migrating[vm_instance.id] = vm_instance
                    self.__things_changed = True



        elif vm_instance.state == 'resized':
            if vm_instance.new_task_state == None and vm_instance.old_task_state == 'resize_finish':
                self.__migrate_service.schedule_confirm(vm_instance.id)

        elif vm_instance.state == 'deleted':
            if vm_instance.id in self.__vm_instances.keys():
                self.__things_changed = True
                del self.__vm_instances[vm_instance.id]
                if vm_instance.compute_node is not None:
                    vm_instance.compute_node.remove_from_vm_active(vm_instance.id)
                    vm_instance.compute_node.remove_from_vm_migrating(vm_instance.id)

        elif vm_instance.state == 'error':
            print('INFO: Instance %s is in error state' % (vm_instance.display_name))

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

        self.vm_active = {}
        self.vm_migrating = {}

        # self.lock = Lock()

    def remove_from_vm_active(self, vm_id):
        instance = None
        if vm_id in self.vm_active.keys():
            instance = self.vm_active[vm_id]
            del self.vm_active[vm_id]
        return instance

    def remove_from_vm_migrating(self, vm_id):
        instance = None
        if vm_id in self.vm_migrating.keys():
            instance = self.vm_migrating[vm_id]
            del self.vm_migrating[vm_id]
        return instance

    def check_for_overload(self):
        print('TO DO: Not yet implemented !')

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

    #
    #   Method that will check if vm instance is overloaded
    #   If overload is detected vm needs to be migrated to another
    #   compute node
    #
    def check_for_overload(self):
        print('TO DO: Not yet implemented !')


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
