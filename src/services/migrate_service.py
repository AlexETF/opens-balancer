
import sys
import logging
from novaclient import client
from keystoneclient import session
from threading import Thread
from threading import Lock
from config import config

CONFIRM_RESIZE_STATE = 'VERIFY_RESIZE'

""" Parametri za live migraciju """
BLOCK_MIGRATION = config.live_migrate_opts['block_migration']
DISK_OVER_COMMIT = config.live_migrate_opts['disk_over_commit']

class MigrateService(object):
    """ Klasa za migraciju instanci. Cuva informacije o trenutnim migracijama.
        Pokrece nit u kojoj se vrsi stvarno slanje zahtjeva za migraciju instance.  """

    def __init__(self, auth_service, logger = None):
        self.__lock = Lock()
        self.__migrating_tasks = {}
        self.__auth_service = auth_service

        self.logger = logger or logging.getLogger(__name__)

    @property
    def auth_service(self):
        return self.__auth_service

    def __check_if_task_exists(self, server_id):
        """" Provjera da li postoji informacija o migraciji instance sa ID server_id """
        if server_id in self.__migrating_tasks.keys():
            return  True
        return False

    def task_done(self,server_id):
        """ Brise informaciju o migraciji instance """
        self.__lock.acquire()
        if server_id in self.__migrating_tasks.keys():
            del self.__migrating_tasks[server_id]
            self.logger.debug('Deleted migrate task ID %s' % server_id)
        self.__lock.release()

    def get_migrating_vms_to_host(self, node_id):
        """ Vraca ID instanci koje se migriraju na hosta sa ID node_id """
        result = []
        for server_id in self.__migrating_tasks.keys():
            if self.__migrating_tasks[server_id] == node_id:
                result.append(server_id)
        return result

    def schedule_live_migration(self, server_id, node):
        """ Kreira nit za migraciju instance """
        self.__lock.acquire()
        if self.__check_if_task_exists(server_id) == True:
            self.__lock.release()
            return False
        else:
            worker = LiveMigrationThread(server_id = server_id, host = node.host, migrate_service = self, logger = self.logger)
            self.__migrating_tasks[server_id] = node.id
            worker.setDaemon(True)
            worker.start()
            self.__lock.release()
            return True

class LiveMigrationThread(Thread):
    """ Nit za pokretanje live migracije """

    def __init__(self, server_id, host, migrate_service, logger = None):
        Thread.__init__(self)
        self.__server_id = server_id
        self.__host = host
        self.__migrate_service = migrate_service

        self.logger = logger or logging.getLogger(__name__)

    def run(self):
        try:
            sess = self.__migrate_service.auth_service.get_session()
            version = self.__migrate_service.auth_service.get_nova_api_version()
            novaclient = client.Client(version, session = sess)
            server = novaclient.servers.find(id = self.__server_id)
            novaclient.servers.live_migrate(server = server, host = self.__host, block_migration = BLOCK_MIGRATION, disk_over_commit = DISK_OVER_COMMIT)
            self.logger.info('Scheduled live migration of server %s ID: %s' % (server.name, server.id))
        except Exception as e:
            self.logger.error('Failed live migration of server ID: %s' % (self.__server_id))
            self.logger.exception(e)
            self.__migrate_service.task_done(self.__server_id)
