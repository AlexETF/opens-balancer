from time import sleep
import random
from config import credentials
from services.auth_service import AuthService
from services.migrate_service import MigrateService
from novaclient.v2 import Client
from threading import Timer

start_interval  = 10   #interval (10min)
delete_interval = 12   #interval (12min)
max_instances = 10


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

def start_instances():
   """Your CODE HERE"""
   client = Client(session = auth_service.get_session())
   servers  = client.servers.list()
   print('Starting %d' % random.randrange(len(servers)))
   Timer(start_interval, start_instances).start()

def delete_instances():
    """Your CODE HERE"""
    client = Client(session = auth_service.get_session())
    servers  = client.servers.list()
    print('Deleting %d' % random.randrange(len(servers)))
    Timer(delete_interval, delete_instances).start()




Timer(start_interval, start_instances).start()
Timer(delete_interval, delete_instances).start()
