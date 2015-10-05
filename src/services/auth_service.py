import logging
from keystoneclient import session
from keystoneclient.auth.identity import v3

class AuthService(object):

    def __init__(self, keystone_url, username, password, user_domain_name, project_name, project_domain_name,
                 nova_api_version, logger = None):
        self.__keystone_url = keystone_url
        self.__username = username
        self.__password = password
        self.__user_domain_name = user_domain_name
        self.__project_name = project_name
        self.__project_domain_name = project_domain_name
        self.__nova_api_version = nova_api_version
        self.__auth = v3.Password(auth_url = self.__keystone_url,
                                  username = self.__username,
                                  password = self.__password,
                                  user_domain_name = self.__user_domain_name,
                                  project_name = self.__project_name,
                                  project_domain_name = self.__project_domain_name)
        self.__session = None
        self.logger = logger or logging.getLogger(__name__)

    def get_session(self):
        self.__session = session.Session(auth = self.__auth)
        return self.__session

    def get_nova_api_version(self):
        return self.__nova_api_version

    def invalidate_session(self):
        self.__session.invalidate(auth = self.__session.auth)
        self.__session = None
