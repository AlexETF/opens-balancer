import logging
from config import config
from services import filters


class RamFilter(filters.BaseFilter):

    def __init__(self, logger = None):
        filters.BaseFilter.__init__(self)
        self.ram_weight = config.weights.get('ram', 1)
        self.logger = logger or logging.getLogger(__name__)

    def filter_one(self, host, vm):
        """ Vraca True ako host ima dovoljno RAM memorije za instancu, inace False """
        free_ram_mb = host.free_ram_mb
        required_ram_mb = vm.memory_mb
        if required_ram_mb > free_ram_mb:
            self.logger.error("Host %s doesn't have enough RAM memory. Required %d MB, available %d MB"
                              % (host.hypervisor_hostname, required_ram_mb, free_ram_mb))
            return False
        return True

    def overloaded(self, host):
        """ Vraca True ako host nema vise slobodne RAM memorije, inace False """
        free_ram_mb = host.free_ram_mb
        if free_ram_mb > 0:
            return False
        return True

    def weight_host(self, host):
        """ Racuna opterecenje hosta """
        ram_ratio = (host.memory_mb_used * 100.0) / host.memory_mb
        return ram_ratio * self.ram_weight

    def weight_instance_on_host(self, host, vm):
        """" Racuna opterecenje koje instanca pravi na hostu """
        ram_ratio = (vm.memory_mb * 100.0) / host.memory_mb
        return ram_ratio * self.ram_weight

    def get_weight(self):
        """ Vraca faktor tezine za RAM memoriju """
        return self.ram_weight
