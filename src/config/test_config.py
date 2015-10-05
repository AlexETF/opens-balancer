#
#    Konfiguracioni fajl za testnu skriptu TEST - scheduled_start_delete.py
#
#
scheduled_times = {
                    'start_interval' : 10 * 60,
                    'delete_interval' : 15 * 60,
                    'deviation'       : 60
                  }

instance_properties = {
                       'flavor_name' :   'm1.micro',
                       'image_name'  :   'TestVM',
                       'availability_zone'   :   'nova',
                       'hosts' : {
                                    'host_to_start' :   'node-4',
                                    'host_to_delete'   :   'node-2'
                                 },
                        'max_instances' :   6,
                        'default_number_of_intances' : 2

}
