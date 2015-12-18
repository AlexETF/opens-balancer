import sys
import random
from time import time
from config import credentials, test_config
from services.auth_service import AuthService
from novaclient import client

def main():

    flavor_name = test_config.instance_properties['flavor_name']
    image_name = test_config.instance_properties['image_name']
    availability_zone = test_config.instance_properties['availability_zone']

    DEFAULT = test_config.instance_properties['default_number_of_instances']

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

    VERSION = credentials.keystone_cfg['nova_api_version']

    auth_service = AuthService(keystone_url=keystone_url,
                               username = username,
                               password = password,
                               user_domain_name = user_domain_name,
                               project_name = project_name,
                               project_domain_name = project_domain_name,
                               nova_api_version = VERSION)

    try:
        print('Authenticating, waiting server to respond')
        nova = client.Client(VERSION, session=auth_service.get_session())
        print('Getting desired flavor %s' % flavor_name)
        flavor = nova.flavors.find(name = flavor_name)
        print('Getting desired image %s' % image_name)
        image = nova.images.find(name = image_name)
        print('Getting network list')
        networks = nova.networks.list()
        print('Creating nic with network id %s' % networks[0].id)
        nics = [{'net-id' : networks[0].id}]

        for i in range(num_instances):
            name = 'random ' + str(i) + str(time())
            print('Starting server %s' % name)
            server = nova.servers.create(name = name,
                                            image = image.id,
                                            flavor = flavor.id,
                                            nics = nics,
                                            availability_zone = availability_zone)
    except Exception as e:
        print e

    print 'Finished ...'

if __name__ == '__main__':
    main()
