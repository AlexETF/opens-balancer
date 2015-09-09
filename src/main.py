
#    Goal is to migrate one instance from controller node
#    to another separate compute node running on it's
#    own virtual server.
#

#from keystoneclient.v3 import client
from keystoneclient import session
from keystoneclient.auth.identity import v3

from novaclient.v2 import client

keystone_url = "http://localhost:5000/v3"
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


hypervisors = nova_client.hypervisors.list()
print(dir(hypervisors[0]))

#for hypervisor in hypervisors:
#    print hypervisor._info

compute = nova_client.hypervisors.find(hypervisor_hostname = 'compute')
print(compute._info)



#servers = nova_client.servers.list()
#for server in servers:
#    print server._info

#server = nova_client.servers.find(name = 'compute-instance')
#print server._info

#nova_client.servers.migrate(server)

#    TEST - Creating instance on controller node
#
flavor = nova_client.flavors.find(ram = 64)
image = nova_client.images.find(name = "cirros-0.3.4-x86_64-uec")
network = nova_client.networks.find(label = "private")

zones = nova_client.availability_zones.list()
for zone in zones:
    print zone._info

zone = nova_client.availability_zones.find(zoneName = 'migrate-zone')
print zone

server = nova_client.servers.create(name = "compute-instance-test2",
                                    image = image.id,
                                    flavor = flavor.id,
                                    network = network.id,
                                    availability_zone = zone.zoneName)

#nova_client.servers.create(name, image, flavor, meta, files, reservation_id, min_count, max_count, security_groups, userdata, key_name, availability_zone, block_device_mapping, block_device_mapping_v2, nics, scheduler_hints, config_drive, disk_config)
while True:
    server = nova_client.servers.find(name = 'compute-instance-test2')
    print server.status
