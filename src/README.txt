Before using application change configuration parameters according to your OpenStack cloud setup.

Configuration files are found in config/ directory.
There are two configuration files:

credentials.py	-	Openstack Keystone service url and credentials
			RabbitMQ service url and credentials


config.py	-	Weights for parameters that are used for weighing compute node workload
			Time after periodic collecting of cloud data will occur (in minutes)
			Minimum time after intance can be migrated again (in minutes)
			Logging options


After configuration start balancer_app.py



For testing we recommend using scripts:

"TEST - delete_servers.py"	   -	used for quick deletion of servers in cloud. Pass to script number of servers to delete,
						otherwise default number is 2.

"TEST - start_servers.py"	   -	used for starting servers in cloud. Pass the script number of servers to start,
					otherwise default number is 2. Default settings:

					flavor_name = 'm1.micro'	# RAM = 64 MB, Disk = 0 GB, Ephemeral disk = 0 GB, VCPUs = 1
					image_name = 'TestVM'	  	# cirros image
					availability_zone = 'nova'

					To change defualt settings, edit lines 10, 11 and 12 in script.

"TEST - scheduled_start_delete.py" -	used for scheduled start and delete tasks of servers. Default time for starting
				      	servers is 10 minutes and for deleting is 15 minutes.
				      	To change that edit lines 9 and 10 in script:

							start_interval  = 10 * 60   #interval (10min)
							delete_interval = 15 * 60   #interval (15min)

					Instances will be spawned with settings:

						flavor_name = 'm1.micro'	# RAM = 64 MB, Disk = 0 GB, Ephemeral disk = 0 GB, VCPUs = 1
						image_name = 'TestVM'		# cirros image
						availability_zone = 'nova'

					To change defualt settings, edit lines 12, 13 and 14 in script.

					There is also limit for number of instances in the cloud.
					Edit line 15 to change default limit.

							max_instances = 7


logs/	-	default directory for storing log files of application


************************************
Author: Aleksandar Vukotić

Elektrotehnički fakultet, Banja Luka
