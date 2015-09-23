import sys
import random
from time import time
from config import credentials
from services.auth_service import AuthService
from novaclient.v2 import Client

DEFAULT = 2

if len(sys.argv) < 2:
    print('INFO: Number of instances is not passed, using DEFAULT = %d' % DEFAULT)
    num_instances = DEFAULT
else:
    try:
        num_instances = int(sys.argv[1])
    except Exception:
        print('ERROR: Invalid argument passed, needs to be integer')
        print('INFO: Using DEFAULT = %d instead' % DEFAULT)
        num_instances = DEFAULT

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
print('Getting desired flavor')
flavor = client.flavors.find(ram = 64)
print('Getting desired image')
image = client.images.find(name = 'TestVM')
print('Getting network list')
networks = client.networks.list()
print('Creating nic with network id %s' % networks[0].id)
nics = [{'net-id' : networks[0].id}]


for i in range(num_instances):
    name = 'random ' + str(i) + str(time())
    print('Starting server %s' % name)
    server = client.servers.create(name = name,
                                    image = image.id,
                                    flavor = flavor.id,
                                    nics = nics,
                                    availability_zone='nova')

print 'Finished ...'
