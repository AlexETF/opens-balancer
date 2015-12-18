#
#    Konfiguracioni fajl za testne skripte
#
#
scheduled_times = {
                    'start_interval' : 5 * 60,
                    'delete_interval' : 8 * 60,
                    'deviation'       : 60
                  }

instance_properties = {
                       'flavor_name' :   'm1.micro',
                       'image_name'  :   'TestVM',
                       'availability_zone'   :   'nova',
                       'hosts' : {
                                    'host_to_start' :   'node-2',
                                    'host_to_delete'   :   'node-3'
                                 },
                        'max_instances' :   6,
                        'default_number_of_instances' : 2

}
