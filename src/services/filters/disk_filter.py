from config import config
from services import filters


class DiskFilter(filters.BaseFilter):

    def __init__(self):
        filters.BaseFilter.__init__(self)
        self.disk_weight = config.weights.get('disk', 1)

    def filter_one(self, host, vm):
        """ Return True if it passes the filter, False otherwise. """
        free_disk_gb = host.free_disk_gb
        required_disk_gb = vm.disk_gb + vm.ephemeral_gb
        if required_disk_gb > free_disk_gb:
            # print ERROR to LOG file
            return False
        return True

    def overloaded(self, host):
        """ Return True if host is overloaded, False otherwise """
        free_disk_gb = host.free_disk_gb
        if free_disk_gb > 0:
            return False
        return True

    def weight_host(self, host):
        """ Return Weight of host based on his parameter """
        return host.local_gb_used * self.disk_weight

    def weight_host_without_vm(self, host, vm):
        if vm.id in host.vm_instances.keys():
            disk_gb = vm.disk_gb + vm.ephemeral_gb
            return (host.local_gb_used - disk_gb) * self.disk_weight
        else:
            return host.local_gb_used * self.disk_weight

    def weight_host_with_vm(self, host, vm):
        disk_gb = vm.disk_gb + vm.ephemeral_gb
        return (host.local_gb_used + disk_gb) * self.disk_weight

    def get_weight(self, host):
        """ Return Weight parameter """
        return self.disk_weight
