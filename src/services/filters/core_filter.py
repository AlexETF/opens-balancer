import logging
from config import config
from services import filters

class CoreFilter(filters.BaseFilter):

    def __init__(self, logger = None):
        filters.BaseFilter.__init__(self)
        self.vcpu_weight = config.weights.get('vcpu', 1)
        self.logger = logger or logging.getLogger(__name__)

    def filter_one(self, host, vm):
        """ Vraca True ako host ima dovoljno VCPU-a za instancu vm, inace vraca False """
        free_vcpus = host.vcpus - host.vcpus_used
        required_vcpus = vm.vcpus
        if  required_vcpus > free_vcpus:
            self.logger.error("Host %s doesn't have enough VCPU-s. Required %d VCPU, available %d VCPU"
                              % (host.hypervisor_hostname, required_vcpus, free_vcpus))
            return False
        return True

    def overloaded(self, host):
        """ Vraca True ako host ima slobodnih VCPU-a, inace False """
        free_vcpus = host.vcpus - host.vcpus_used
        if free_vcpus >= 0:
            return False
        return True

    def weight_host(self, host):
        """ Racuna i vraca opterecenje hosta """
        core_ratio = (host.vcpus_used * 100.0) / host.vcpus
        return core_ratio * self.vcpu_weight

    def weight_instance_on_host(self, host, vm):
        """ Racuna i vraca opterecenje instance na hostu """
        core_ratio = (vm.vcpus * 100.0) / host.vcpus
        return core_ratio * self.vcpu_weight

    def get_weight(self):
        """ Vraca faktor tezine za VCPU """
        return self.vcpu_weight
