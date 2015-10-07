#
#
#   KONFIGURACIONI FAJL ZA AUTENTIFIKACIJU NA KEYSTONE I RABBITMQ SERVIS
#
#

keystone_cfg =  {
                'service_url' : 'http://172.16.0.2:5000/v3',
                'username' : 'admin',
                'password' : 'admin',
                'user_domain_name' : 'default',
                'project_name'     : 'admin',
                'project_domain_name' : 'default',
                'nova_api_version'    : '2.30'
                }

rabbitmq_cfg =  {
                'server_endpoint' : '10.20.0.3',
                'port'      :  5672,
                'username'  : 'nova',
                'password'  : 'SwCSdL00',
                'virtual_host' : '/',
                'listening_options' : {
                                        'exchange_name' : 'nova',
                                        'my_queue_name' : 'nova_listening_queue',
                                        'binding_key'   : '#'
                                      }
                }
