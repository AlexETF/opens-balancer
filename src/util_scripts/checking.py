import json
from time import time
from ..config import credentials
from time import sleep
from services.auth_service import AuthService
from novaclient.v2 import Client
from config import credentials

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

# client = Client(session=auth_service.get_session())
# print("INFO: Initializing RabbitMQMessageService")
# client = Client(session=self.__auth_service.get_session())
# print("INFO: Collecting information about compute nodes")
# items  = client.hypervisors.list(detailed=True)
# print('INFO: Collecting information about services')
# items = client.services.list()
# dict = {'status': null}
# print dict['status'] == None
# print("INFO: Collecting information about VMs")
# items  = client.servers.list(detailed=True)
# for item in items:
#     # item = item.to_dict()
#     # print item['OS-EXT-STS:task_state']
#     print json.dumps(item.to_dict(), indent=4, sort_keys=4, separators=(',', ': '))
