from config import config
from services import filters

class CoreFilter(filters.BaseFilter):

    def __init__(self):
        filters.BaseFilter.__init__(self)
        self.vcpu_weight = config.weights.get('vcpu', 1)

    def filter_one(self, host, vm):
        """Return True if it passes the filter, False otherwise. """
        free_vcpus = host.vcpus - host.vcpus_used
        required_vcpus = vm.vcpus
        if  required_vcpus >= free_vcpus:
            # print to LOG file ERROR
            return False
        return True

    def overloaded(self, host):
        """ Return True is host is overloaded, False otherwise """
        free_vcpus = host.vcpus - host.vcpus_used
        if free_vcpus > 0:
            return False
        return True

    def weight_host(self, host):
        """ Return Weight of host based on his parameter """
        return host.vcpus_used * self.vcpu_weight

    def get_weight(self):
        """ Return Weight parameter """
        return self.vcpu_weight
