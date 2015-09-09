
#    Goal is to migrate one instance from controller node
#    to another separate compute node running on it's
#    own virtual server.
#

#from keystoneclient.v3 import client
from keystoneclient import session
from keystoneclient.auth.identity import v3

from novaclient.v2 import client

keystone_url = "http://172.16.0.2:5000/v3"
username = "admin"
password = "admin"
user_domain_name = "default"
project_name = "admin"
project_domain_name = "default"


auth = v3.Password(auth_url = keystone_url,
                   username = username,
                   password = password,
                   user_domain_name = user_domain_name,
                   project_name = project_name,
                   project_domain_name = project_domain_name)


sess = session.Session(auth = auth)

nova_client = client.Client(session = sess)

print(nova_client.servers.list())
print(nova_client.flavors.list())


server = nova_client.servers.find(name='testing-7a5f391f-3a8a-42d5-accd-17440e169d66')

# nova_client.servers.migrate(server=server)
# while True:
#     server = nova_client.servers.find(name = 'testing-7a5f391f-3a8a-42d5-accd-17440e169d66')
#     if server.status == 'VERIFY_RESIZE':
#         nova_client.servers.confirm_resize(server = server)
#         break
#     print server.status
#
# server = nova_client.servers.find(name = 'testing-7a5f391f-3a8a-42d5-accd-17440e169d66')
# print server.status
