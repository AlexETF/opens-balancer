#
#
#       CONFIGURATION FILE FOR WEIGHTS
#
#       Filters use the weights for weighting host
#       based upon host parameter
#
#       IMPORTANT: Weights need to be a POSITIVE REAL NUMBER
#
#
weights = {
           'vcpu' : 10.0,
           'ram'  : 0.01,
           'disk' : 1.0
          }

periodic_check_interval = 3 * 60        # enter time in sec

migrate_time = 1 * 60                   # enter time in sec

log_directory = './logs/'               # path to log files directory
log_max_bytes = 100 * 1024 * 1024       # 100MB limit size for log file
log_backup_count = 1                    # num of log file copies
