import sys
import os
from time import sleep
from nova_migrate import AuthService, MigrateService
from novaclient.v2 import client
import json
from keystoneclient import session
from keystoneclient.auth.identity import v3

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

nova = client.Client(session = sess)

hosts = nova.hosts.list()
for host in hosts:
    print(host.to_dict())

hypervisors = nova.hypervisors.list()
for i in hypervisors:
    print(i.to_dict())
