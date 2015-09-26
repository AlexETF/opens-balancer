Before using application change configuration parameters according to your OpenStak cloud setup.

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

"TEST - delete_servers.py"		-	used for quick deletion of servers in cloud. Pass to script number of servers to delete, 
									otherwise default number is 2.

"TEST - start_servers.py"		-	used for starting servers in cloud. Pass the script number of servers to start, 
									otherwise default number is 2.

"TEST - scheduled_start_delete.py"	-	used for scheduled start and delete tasks of servers. Default time for starting 
										servers is 10 minutes and for deleting is 15 minutes. 
										To change that edit 10 and 11 line in script:

											start_interval  = 10 * 60   #interval (10min)
											delete_interval = 15 * 60   #interval (15min)



logs/	-	default directory for storing log files of application



************************************
Author: Aleksandar Vukotić
	
Elektrotehnički fakultet, Banja Luka
						
						
					 
		  
