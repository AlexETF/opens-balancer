import logging
from config import config
from services import filters


class DiskFilter(filters.BaseFilter):

    def __init__(self, logger = None):
        filters.BaseFilter.__init__(self)
        self.disk_weight = config.weights.get('disk', 1)
        self.logger = logger or logging.getLogger(__name__)

    def filter_one(self, host, vm):
        """ Vraca True ako host ima dovoljno slobodnog diska u GB za instancu vm, inace vraca False  """
        free_disk_gb = host.free_disk_gb
        required_disk_gb = vm.disk_gb + vm.ephemeral_gb
        if required_disk_gb > free_disk_gb:
            self.logger.error("Host %s doesn't have enough disk space. Required %d GB, available %d GB"
                              % (host.hypervisor_hostname, required_disk_gb, free_disk_gb))
            return False
        return True

    def overloaded(self, host):
        """ Vraca True ako host nema vise slobodnog disk prostora, inacec False """
        free_disk_gb = host.free_disk_gb
        if free_disk_gb > 0:
            return False
        return True

    def weight_host(self, host):
        """ Racuna opterecenje hosta  """
        disk_ratio = (host.local_gb_used * 100.0) / host.local_gb
        return disk_ratio * self.disk_weight

    def weight_instance_on_host(self, host, vm):
        """" Racuna opterecenje instance na hostu """
        disk_gb = vm.disk_gb + vm.ephemeral_gb
        disk_ratio =  (disk_gb * 100.0) / host.local_gb
        return disk_ratio * self.disk_weight

    def get_weight(self, host):
        """ Vraca faktor tezine za disk """
        return self.disk_weight
