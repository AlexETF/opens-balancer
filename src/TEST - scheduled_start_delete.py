import random
import sys
from time import time
from config import credentials
from services.auth_service import AuthService
from novaclient.v2 import Client
from threading import Timer

start_interval  = 10 * 60   #interval (10min)
delete_interval = 15 * 60   #interval (15min)

deviation = 60

flavor_name = 'm1.micro'
image_name = 'TestVM'
availability_zone = 'nova'
max_instances = 7

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

auth_service = AuthService(keystone_url=keystone_url,
                           username=username,
                           password = password,
                           user_domain_name = user_domain_name,
                           project_name=project_name,
                           project_domain_name=project_domain_name)

print('Authenticating, waiting server to respond')
client = Client(session = auth_service.get_session())
print('Getting desired flavor %s' % flavor_name)
flavor = client.flavors.find(name = flavor_name)
print('Getting desired image %s' % image_name)
image = client.images.find(name = image_name)
print('Getting network list')
networks = client.networks.list()
print('Creating nic')
nics = [{'net-id' : networks[0].id}]

def start_instances():
   """ Scheduled task for starting random number of instances """
   client = Client(session = auth_service.get_session())
   servers  = client.servers.list()
   if len(servers) >= max_instances:
       print('INFO: Already too much servers')
       start_timer_start()
       return
   random_num = random.randrange(3) + 1
   for i in range(random_num):
       name = 'random-' + str(i) + ', ' + str(time())
       print('Starting %s' % name)
       server = client.servers.create(name = name,
                                      image = image.id,
                                      flavor = flavor.id,
                                      nics = nics,
                                      availability_zone = availability_zone)
   start_timer_start()

def delete_instances():
    """ Scheduled task for deleting random number of instances """
    client = Client(session = auth_service.get_session())
    servers  = client.servers.list()
    num_of_instances = len(servers)
    if num_of_instances == 0:
        print('INFO: No servers to delete')
        start_timer_delete()
        return
    error_state = False
    for server in servers:
        if server.status == 'ERROR':
            print('INFO: Deleting server %s' % server.name)
            client.servers.delete(server)
            servers.remove(server)
            error_state = True
    if not error_state:
        index = random.randrange(num_of_instances + 1)
        if index == num_of_instances:
            index = index - 1
        print('INFO: Number of servers to delete %d ' % (index))
        for i in range(index):
            print('INFO: Deleting server %s' % servers[i].name)
            client.servers.delete(servers[i])
    start_timer_delete()

start_timer_start()
start_timer_delete()

while True:
    command = raw_input()
    if command == 'q':
        break

print('Finished ...')
