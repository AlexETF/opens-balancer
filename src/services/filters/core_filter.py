import logging
from config import config
from services import filters

class CoreFilter(filters.BaseFilter):

    def __init__(self, logger = None):
        filters.BaseFilter.__init__(self)
        self.vcpu_weight = config.weights.get('vcpu', 1)
        self.logger = logger or logging.getLogger(__name__)

    def filter_one(self, host, vm):
        """Return True if it passes the filter, False otherwise. """
        free_vcpus = host.vcpus - host.vcpus_used
        required_vcpus = vm.vcpus
        if  required_vcpus > free_vcpus:
            self.logger.error("Host %s doesn't have enough VCPU-s. Required %d VCPU, available %d VCPU"
                              % (host.hypervisor_hostname, required_vcpus, free_vcpus))
            return False
        return True

    def overloaded(self, host):
        """ Return True is host is overloaded, False otherwise """
        free_vcpus = host.vcpus - host.vcpus_used
        if free_vcpus >= 0:
            return False
        return True

    def weight_host(self, host):
        """ Return Weight of host based on his parameter """
        core_ratio = (host.vcpus_used * 100.0) / host.vcpus
        return core_ratio * self.vcpu_weight

    def weight_host_without_vm(self, host, vm):
        if vm.id in host.vm_instances.keys():
            core_ratio = ((host.vcpus_used - vm.vcpus) * 100.0) / host.vcpus
        else:
            core_ration = (host.vcpus_used * 100.0) / host.vcpus
        return core_ratio * self.vcpu_weight

    def weight_host_with_vm(self, host, vm):
        core_ratio = ((host.vcpus_used + vm.vcpus) * 100.0) / host.vcpus
        return core_ratio * self.vcpu_weight

    def get_weight(self):
        """ Return Weight parameter """
        return self.vcpu_weight
