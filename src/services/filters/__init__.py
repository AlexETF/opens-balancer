

class BaseFilter(object):

    def filter_one(self, host, vm):
        """ Vraca True ako host ima resursa za instancu vm, inace vraca False.
            Redefinisati u podklasi.
        """
        return True

    def overloaded(self, host):
        """ Vraca True ako host ima resursa, inace False.
            Redefinisati u podklasi
        """
        return True

    def weight_host(self, host):
        """ Racuna i vraca tezinu hosta.
            Redefinisati u podklasi.
        """
        return 0

    def weight_instance_on_host(self, host, vm):
        """ Racuna i vraca tezinu instance na hostu.
            Redefinisati u podklasi.
        """
        return 0

    def get_weight(self):
        """ Vraca fator tezine
            Redefinisati u podklasi.
        """
        return 0

    def filter_all(self, filter_host_list, vm):
        """ Vraca listu hostova koji imaju dovoljno resursa za instancu vm """
        filtered = []
        for host in filter_obj_list:
            if self.filter_one(host = host, vm = vm):
                filtered.append(host)
