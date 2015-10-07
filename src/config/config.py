#
#
#       KONFIGURACIONI FAJL ZA FILTERE I LOGER
#
#       Filteri koriste tezine da bi odredili tezinu hosta
#       na osnovu odgovarajuceg parametra
#
#       VAZNO: Ove vrijednosti moraju biti pozitivni realni brojevi 
#
#
weights = {
           'vcpu' : 1.2,
           'ram'  : 1.0,
           'disk' : 1.0
          }

periodic_check_interval = 3 * 60        # vrijeme za koje ce biti pokrenuto periodicno prikupljanje
                                        # informacija o stanju clouda

migrate_time = 5 * 60                   # minimalno vrijeme nakon kojeg virtuelna masina moze biti ponovo
                                        # migrirana

log_directory = './logs/'               # putanja do foldera gdje ce biti skladisteni log fajlovi
log_tags = {
            'sys_info'         : 'SYS_INFO',                 # informacije o tome sta sistem trenutno radi
            'total_info'       : 'TOTAL_VMS',                # ukupan broj masina
            'node_info'        : 'NODE_INFO',                # broj vm na jednom cvoru
            'vm_info'          : 'VM_INFO',                  # status virtuelne masine
            'migration_started' : 'MIGRATION_STARTED',      # migracija pokrenuta
            'migration_ended' : 'MIGRATION_ENDED'           # migracija potvrdjena

}
log_tag_separator = '|'
