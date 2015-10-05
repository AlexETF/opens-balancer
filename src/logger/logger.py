import logging
from config import config
from logging import FileHandler, Formatter
from time import gmtime, strftime, localtime

LOG_TAGS = config.log_tags
LOG_DIRECTORY = config.log_directory
SEPARATOR = config.log_tag_separator

class CloudLogger(logging.Logger):

    def __init__(self, name, level = logging.DEBUG):
        logging.Logger.__init__(self, name, level)

        log_filename = LOG_DIRECTORY + str(strftime("%Y-%m-%d %Hh%Mm%Ss", localtime())) + '.log'
        handler = FileHandler(filename = log_filename)
        formatter = Formatter('%(asctime)s' + SEPARATOR + '%(relativeCreated)d' + SEPARATOR + '%(message)s')
        handler.setFormatter(formatter)
        self.addHandler(handler)

    def special(self, msg, *args, **kwargs):
        self.log(self.level, msg, *args, **kwargs)

    def error(self, obj, *args, **kwargs):
        super(CloudLogger, self).error(LOG_TAGS['sys_info'] + SEPARATOR + str(obj), *args, **kwargs)

    def debug(self, message):
        super(CloudLogger, self).debug(LOG_TAGS['sys_info'] + SEPARATOR + message)

    def info(self, message):
        super(CloudLogger, self).debug(LOG_TAGS['sys_info'] + SEPARATOR + message)

    def warning(self, message):
        super(CloudLogger, self).warning(LOG_TAGS['sys_info'] + SEPARATOR + message)

    def sys_info(self, message):
        super(CloudLogger, self).info(LOG_TAGS['sys_info'] + SEPARATOR + message)

    def total_info(self, message):
        super(CloudLogger, self).info(LOG_TAGS['total_info'] + SEPARATOR + message)

    def node_info(self, message):
        super(CloudLogger, self).info(LOG_TAGS['node_info'] + SEPARATOR + message)

    def vm_info(self, message):
        super(CloudLogger, self).info(LOG_TAGS['vm_info'] + SEPARATOR + message)

    def migration_started(self, message):
        super(CloudLogger, self).info(LOG_TAGS['migration_started'] + SEPARATOR + message)

    def migration_confirmed(self, message):
        super(CloudLogger, self).info(LOG_TAGS['migration_confirmed'] + SEPARATOR + message)
