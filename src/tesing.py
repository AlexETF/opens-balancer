from config import config, credentials
import logging, logging.handlers
from time import gmtime, strftime, localtime, sleep
from services.auth_service import AuthService
from novaclient.v2 import Client
from exceptions import KeyboardInterrupt

from services.auth_service import AuthService

def setup_logging():
    """ Method for configuring application logger options """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    log_filename = config.log_directory + str(strftime("%Y-%m-%d %Hh%Mm%Ss", localtime())) + '.log'
    max_bytes = config.log_max_bytes
    backup_count = config.log_backup_count
    handler = logging.handlers.RotatingFileHandler(log_filename, maxBytes=max_bytes, backupCount=backup_count)
    formatter = logging.Formatter('%(asctime)s|%(relativeCreated)d|%(levelname)s|%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

def get_auth_service():

    keystone_url = credentials.keystone_cfg['service_url']
    username = credentials.keystone_cfg['username']
    password = credentials.keystone_cfg['password']
    user_domain_name = credentials.keystone_cfg['user_domain_name']
    project_name = credentials.keystone_cfg['project_name']
    project_domain_name =  credentials.keystone_cfg['project_domain_name']

    auth_service = AuthService(keystone_url = keystone_url,
                               username = username,
                               password = password,
                               user_domain_name = user_domain_name,
                               project_name = project_name,
                               project_domain_name = project_domain_name)

    return auth_service

def main():
    # logger =  setup_logging()
    auth_service = get_auth_service()
    client = Client(session = auth_service.get_session())
    servers = client.servers.list()
    # print dir(servers[0])
    print servers[0].to_dict()['OS-EXT-SRV-ATTR:host']


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print('EXIT TASK - CTRL + C Pressed')
    print('Finished')
