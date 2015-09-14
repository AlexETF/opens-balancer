from keystoneclient import session
from keystoneclient.auth.identity import v3

class AuthService(object):

    def __init__(self, keystone_url, username, password,
    user_domain_name, project_name, project_domain_name):
        self.keystone_url = keystone_url
        self.username = username
        self.password = password
        self.user_domain_name = user_domain_name
        self.project_name = project_name
        self.project_domain_name = project_domain_name
        self.session = None

    def get_session(self):
        self.auth = v3.Password(auth_url = self.keystone_url,
                           username = self.username,
                           password = self.password,
                           user_domain_name = self.user_domain_name,
                           project_name = self.project_name,
                           project_domain_name = self.project_domain_name)
        self.session = session.Session(auth = self.auth)
        return self.session

    def invalidate_session(self):
        self.session.invalidate(auth = self.session.auth)
        self.session = None
