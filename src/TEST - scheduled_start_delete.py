import random
import sys
from time import time
from config import test_config
from config import credentials
from services.auth_service import AuthService
from novaclient import client
from threading import Timer

""" Konfiguracioni parametri """

start_interval  = test_config.scheduled_times['start_interval']
delete_interval = test_config.scheduled_times['delete_interval']

deviation = test_config.scheduled_times['deviation']

flavor_name = test_config.instance_properties['flavor_name']
image_name = test_config.instance_properties['image_name']
availability_zone = test_config.instance_properties['availability_zone']
host_to_start_instances =  test_config.instance_properties['hosts']['host_to_start']
host_to_delete_instances = test_config.instance_properties['hosts']['host_to_delete']

max_instances = test_config.instance_properties['max_instances']


def start_timer_start():
    start_time  = random.gauss(start_interval, deviation)
    timer = Timer(start_time, start_instances)
    timer.setDaemon(True)
    timer.start()
    print('Scheduled start timer task %d sec' % (start_time))

def start_timer_delete():
    delete_time = random.gauss(delete_interval, deviation)
    timer = Timer(delete_time, delete_instances)
    timer.setDaemon(True)
    timer.start()
    print('Scheduled delete timer task %d sec' % (delete_time))

keystone_url = credentials.keystone_cfg['service_url']
username = credentials.keystone_cfg['username']
password = credentials.keystone_cfg['password']
user_domain_name = credentials.keystone_cfg['user_domain_name']
project_name = credentials.keystone_cfg['project_name']
project_domain_name =  credentials.keystone_cfg['project_domain_name']

VERSION = credentials.keystone_cfg['nova_api_version']

auth_service = AuthService(keystone_url = keystone_url,
                           username = username,
                           password = password,
                           user_domain_name = user_domain_name,
                           project_name = project_name,
                           project_domain_name = project_domain_name,
                           nova_api_version = VERSION)
try:
    print('Authenticating, waiting server to respond')
    novaclient = client.Client(VERSION, session = auth_service.get_session())
    print('Getting desired flavor %s' % flavor_name)
    flavor = novaclient.flavors.find(name = flavor_name)
    print('Getting desired image %s' % image_name)
    image = novaclient.images.find(name = image_name)
    print('Getting network list')
    networks = novaclient.networks.list()
    print('Creating nic')
    nics = [{'net-id' : networks[0].id}]

except Exception as e:
    print e
    sys.exit(1)

def start_instances():
   """ Metoda koja se periodicno pokrece za startovanje instanci na odredjeni compute cvor """
   try:
       novaclient = client.Client(auth_service.get_nova_api_version(), session = auth_service.get_session())
       servers  = novaclient.servers.list()
       if len(servers) >= max_instances:
           print('INFO: Already too much servers')
           start_timer_start()
           return
       random_num = random.randrange(3) + 1
       if (len(servers) + random_num) >= max_instances:
           random_num = max_instances - len(servers)

       for i in range(random_num):
           name = 'random-' + str(i) + ', ' + str(time())
           print('Starting %s' % name)
           server = novaclient.servers.create(name = name,
                                              image = image.id,
                                              flavor = flavor.id,
                                              nics = nics,
                                              availability_zone = availability_zone + ':' + host_to_start_instances)
       start_timer_start()

   except Exception as e:
       print e
       start_timer_start()


def delete_instances():
    """ Metoda koja se periodicno pokrece za brisanje instanci sa odredjenog compute cvora """
    try:
        novaclient = client.Client(auth_service.get_nova_api_version(), session = auth_service.get_session())
        servers = novaclient.servers.list()
        filtered_servers = []
        for server in servers:
            if server.to_dict()['OS-EXT-SRV-ATTR:host'] == host_to_delete_instances:
                filtered_servers.append(server)
        servers = filtered_servers
        num_of_instances = len(servers)
        if num_of_instances == 0:
            print('INFO: No servers to delete')
            start_timer_delete()
            return
        index = random.randrange(num_of_instances) + 1
        if index == num_of_instances:
            index = index - 1
        print('INFO: Number of servers to delete %d ' % (index))
        for i in range(index):
            print('INFO: Deleting server %s' % servers[i].name)
            novaclient.servers.delete(servers[i])

        start_timer_delete()
    except Exception as e:
        print e
        start_timer_delete()

start_timer_start()
start_timer_delete()

while True:
    command = raw_input()
    if command == 'q':
        break

print('Finished ...')
