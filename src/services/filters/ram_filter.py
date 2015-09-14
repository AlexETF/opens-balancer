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
        return host.memory_mb_used * self.ram_weight

    def weight_host_without_vm(self, host, vm):
        if vm.id in host.vm_instances.keys():
            return (host.memory_mb_used - vm.memory_mb) * self.ram_weight
        else:
            return host.memory_mb_used *  self.ram_weight

    def weight_host_with_vm(self, host, vm):
        return (host.memory_mb_used + vm.memory_mb) * self.ram_weight

    def get_weight(self):
        """ Return Weight parameter """
        return self.ram_weight
