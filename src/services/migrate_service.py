
import sys
from novaclient.v2 import client
from keystoneclient import session
from threading import Thread
from threading import Lock

class MigrateService(object):

    def __init__(self, auth_service, logger = None):
        self.__lock = Lock()
        self.__migrating_tasks = []
        self.__confirm_tasks = []
        self.__auth_service = auth_service

        self.logger = logger or logging.getLogger(__name__)

    @property
    def auth_service(self):
        return self.__auth_service

    def __check_if_task_exists(self, server_id):
        if server_id in self.__migrating_tasks:
            return  True
        return False

    def __check_if_confirm_task_exists(self, server_id):
        if server_id in self.__confirm_tasks:
            return  True
        return False
    #
    #   Method used to remove migrate task from running task dictionary
    #   MIGRATE THREADS SHOULD ONLY CALL THIS METHOD WHEN THEY FINISH
    #   MIGRATING THE SERVER
    #
    def task_done(self,server_id):
        self.__lock.acquire()
        if server_id in self.__migrating_tasks:
            self.__migrating_tasks.remove(server_id)
        self.__lock.release()

    def confirm_task_done(self,server_id):
        if server_id in self.__confirm_tasks:
            self.__confirm_tasks.remove(server_id)
            print self.__confirm_tasks

    def schedule_migrate(self, server_id, node):
        self.__lock.acquire()
        if self.__check_if_task_exists(server_id) == True:
            print('INFO: Already exits migrating task')
            self.__lock.release()
            return False
        else:
            worker = MigrationThread(server_id = server_id, migrate_service = self)
            self.__migrating_tasks.append(server_id)
            worker.setDaemon(True)
            worker.start()
            self.__lock.release()
            return True

    def schedule_live_migration(self, server_id, node):
        self.__lock.acquire()
        if self.__check_if_task_exists(server_id) == True:
            print('INFO: Already exits migrating task')
            self.__lock.release()
            return False
        else:
            worker = LiveBlockMigrationThread(server_id = server_id, host = node.host, migrate_service = self)
            self.__migrating_tasks.append(server_id)
            worker.setDaemon(True)
            worker.start()
            self.__lock.release()
            return True

    def schedule_confirm(self, server_id):
        if self.__check_if_confirm_task_exists(server_id) == True:
            print('INFO: Already exits confirm task')
            return False
        else:
            worker = ConfirmThread(server_id = server_id, migrate_service = self)
            self.__confirm_tasks.append(server_id)
            worker.setDaemon(True)
            worker.start()
            return True

#
#   Worker thread for migrating instance
#
class MigrationThread(Thread):

    def __init__(self, server_id, migrate_service):
        Thread.__init__(self)
        self.__server_id = server_id
        self.__migrate_service = migrate_service

    def run(self):
        try:
            sess = self.__migrate_service.auth_service.get_session()
            nova_client = client.Client(session = sess)
            server = nova_client.servers.find(id=self.__server_id)
            nova_client.servers.migrate(server = server)
            print('INFO: Scheduled migration of server %s ID: %s' % (server.name, server.id))

        except Exception as e:
            print e
            print('ERROR:    Failed to migrate server ID: %s' % (self.__server_id))
            self.__migrate_service.task_done(self.__server_id)



#
#   Worker thread for live block migration of vm instance
#
class LiveBlockMigrationThread(Thread):

        def __init__(self, server_id, host, migrate_service):
            Thread.__init(self)
            self.__server_id = server_id
            self.__host = host
            self.__migrate_service = migrate_service

        def run(self):
            try:
                sess = self.__migrate_service.auth_service.get_session()
                nova_client = client.Client(session = sess)
                server = nova_client.servers.find(id = self.__server_id)
                nova_client.servers.live_migrate(server = server, host = self.__host, block_migration = True)
                print('INFO: Scheduled live migration of server %s ID: %s' % (server.name, server.id))
                self.__migrate_service.task_done(self.__server_id)
            except Exception as e:
                print e
                print('ERROR:    Failed live migration of server ID: %s' % (self.__server_id))
                self.__migrate_service.task_done(self.__server_id)



class ConfirmThread(Thread):

        def __init__(self, server_id, migrate_service):
            Thread.__init__(self)
            self.__server_id = server_id
            self.__migrate_service = migrate_service

        def run(self):
            try:
                sess = self.__migrate_service.auth_service.get_session()
                nova_client = client.Client(session = sess)
                server = nova_client.servers.find(id = self.__server_id)
                if server.status == 'VERIFY_RESIZE':
                    nova_client.servers.confirm_resize(server = server)
                    print('INFO: Confirmed migration of server %s ID: %s' % (server.name, server.id))
                    self.__migrate_service.task_done(self.__server_id)
            except Exception as e:
                print e
                print('ERROR:    Failed to confirm migration server ID: %s' % (self.__server_id))
                self.__migrate_service.task_done(self.__server_id)
