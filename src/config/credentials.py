#
#
#   CONFIGURATION FILE FOR AUTHETIFICATION ON KEYSTONE AND RABBITMQ SERVICES
#
#

keystone_cfg =  {
                'service_url' : 'http://172.16.0.2:5000/v3',
                'username' : 'admin',
                'password' : 'admin',
                'user_domain_name' : 'default',
                'project_name'     : 'admin',
                'project_domain_name' : 'default'
                }

rabbitmq_cfg =  {
                'server_endpoint' : '10.20.0.3',
                'port'      :  5672,
                'username'  : 'nova',
                'password'  : 'QNQdh54r',
                'virtual_host' : '/',
                'listening_options' : {
                                        'exchange_name' : 'nova',
                                        'my_queue_name' : 'nova_listening_queue',
                                        'binding_key'   : '#'
                                      }
                }
