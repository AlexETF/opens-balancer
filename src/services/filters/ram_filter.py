import logging
from config import config
from services import filters


class RamFilter(filters.BaseFilter):

    def __init__(self, logger = None):
        filters.BaseFilter.__init__(self)
        self.ram_weight = config.weights.get('ram', 1)
        self.logger = logger or logging.getLogger(__name__)

    def filter_one(self, host, vm):
        """Return True if it passes the filter, False otherwise. """
        free_ram_mb = host.free_ram_mb
        required_ram_mb = vm.memory_mb
        if required_ram_mb > free_ram_mb:
            self.logger.error("Host %s doesn't have enough RAM memory. Required %d MB, available %d MB"
                              % (host.hypervisor_hostname, required_ram_mb, free_ram_mb))
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
        ram_ratio = (host.memory_mb_used * 100.0) / host.memory_mb
        return ram_ratio * self.ram_weight

    def weight_host_without_vm(self, host, vm):
        if vm.id in host.vm_instances.keys():
            ram_ratio = ((host.memory_mb_used - vm.memory_mb) * 100.0) / host.memory_mb
        else:
            ram_ratio = (host.memory_mb_used * 100.0) / host.memory_mb
        return ram_ratio * self.ram_weight

    def weight_host_with_vm(self, host, vm):
        ram_ratio = ((host.memory_mb_used + vm.memory_mb) * 100.0)/ host.memory_mb
        return ram_ratio * self.ram_weight

    def get_weight(self):
        """ Return Weight parameter """
        return self.ram_weight
