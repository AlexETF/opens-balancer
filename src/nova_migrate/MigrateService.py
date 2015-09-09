
import sys
from Queue import Queue
from novaclient.v2 import client
from keystoneclient import session
from threading import Thread
from threading import Lock
from time import sleep
from novaclient.exceptions import NoUniqueMatch

class MigrateService(object):

    def __init__(self, auth_service):
        self.__lock = Lock()
        self.__running_tasks_dict = {}
        self.__auth_service = auth_service

    @property
    def auth_service(self):
        return self.__auth_service

    def __check_if_task_exists(self, server_id):
        if server_id in self.__running_tasks_dict.keys():
            exists = True
        else:
            exists = False
        return exists
    #
    #   Method used to remove migrate task from running task dictionary
    #   MIGRATE THREADS SHOULD ONLY CALL THIS METHOD WHEN THEY FINISH
    #   MIGRATING THE SERVER
    #
    def task_done(self,server_id):
        self.__lock.acquire()
        if server_id in self.__running_tasks_dict.keys():
            del self.__running_tasks_dict[server_id]
        self.__lock.release()

    def revert_migration(self, server_id):
        self.__lock.acquire()
        node =  self.__running_tasks_dict[server_id]
        instance = node.remove_from_vm_migrating(server_id)
        node.vm_active[server_id] = instance
        self.__lock.release()

    def schedule_migrate(self, server_id, node):
        self.__lock.acquire()
        if self.__check_if_task_exists(server_id) == True:
            self.__lock.release()
            return False
        else:
            worker = MigrationThread(server_id = server_id, migrate_service = self)
            self.__running_tasks_dict[server_id] = node
            worker.setDaemon(True)
            worker.start()
            self.__lock.release()
            return True

    def schedule_live_migration(self, server_id, node):
        self.__lock.acquire()
        if self.__check_if_task_exists(server_id) == True:
            self.__lock.release()
            return False
        else:
            worker = LiveBlockMigrationThread(server_id = server_id, host = node.host, migrate_service = self)
            self.__running_tasks_dict[server_id] = node
            worker.setDaemon(True)
            worker.start()
            self.__lock.release()
            return True

    def schedule_confirm(self, server_id):
        worker = ConfirmThread(server_id = server_id, migrate_service = self)
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
        self.__live_block_migration = live_block_migration

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
            self.__migrate_service.revert_migration(self.__server_id)



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

            except Exception as e:
                print e
                print('ERROR:    Failed live migration of server ID: %s' % (self.__server_id))
                self.__migrate_service.task_done(self.__server_id)
                self.__migrate_service.revert_migration(self.__server_id)



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
                nova_client.servers.confirm_resize(server = server)
                print('INFO: Confirmed migration of server %s ID: %s' % (server.name, server.id))
                self.__migrate_service.task_done(self.__server_id)
            except Exception as e:
                print e
                print('ERROR:    Failed to confirm migration server ID: %s' % (self.__server_id))
                self.__migrate_service.task_done(self.__server_id)
