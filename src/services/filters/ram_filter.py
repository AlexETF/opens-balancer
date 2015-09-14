from config import config
from services import filters


class RamFilter(filters.BaseFilter):

    def __init__(self):
        filters.BaseFilter.__init__(self)
        self.ram_weight = config.weights.get('ram', 1)

    def filter_one(self, host, vm):
        """Return True if it passes the filter, False otherwise. """
        free_ram_mb = host.free_ram_mb
        required_ram_mb = vm.memory_mb
        if required_ram_mb > free_ram_mb:
            # print ERROR to log file
            return False
        return True

    def overloaded(self, host):
        """ Return True if host is overloaded, False otherwise """
        free_ram_mb = host.free_ram_mb
        if free_ram_mb > 0:
            return False
        return True

    def weight_host(self, host):
        """ Return Weight of host based on his parameter """
        return host.free_ram_mb * self.ram_weight

    def get_weight(self):
        """ Return Weight parameter """
        return self.ram_weight
