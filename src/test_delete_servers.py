import sys
from config import credentials, test_config
from services.auth_service import AuthService
from novaclient import client


def main():
    
    DEFAULT = test_config.instance_properties['default_number_of_instances']

    if len(sys.argv) < 2:
        print('INFO: Number of instances to delete is not passed, using DEFAULT = %d' % DEFAULT)
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
                               username=username,
                               password = password,
                               user_domain_name = user_domain_name,
                               project_name=project_name,
                               project_domain_name=project_domain_name,
                               nova_api_version = VERSION)

    try:
        print('Authenticating, waiting server to respond')
        novaclient = client.Client(VERSION, session = auth_service.get_session())
        print('Waiting for server list ')
        servers  = novaclient.servers.list()
        total_num = len(servers)

        print('Total number of servers %d' % total_num)
        if total_num < num_instances:
            num_instances = total_num
        print('Number of instances to delete %d' % num_instances)

        for i in range(num_instances):
            print('Deleting server %s ' % servers[i].name)
            novaclient.servers.delete(servers[i])
    except Exception as e:
        print e

    print 'Finished ...'

if __name__ == '__main__':
    main()
