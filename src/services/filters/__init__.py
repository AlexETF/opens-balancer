

class BaseFilter(object):

    def filter_one(self, host, vm):
        """ Return True if it passes the filter, False otherwise.
            Override this in a subclass.
        """
        return True

    def overloaded(self, host):
        """ Return True if it passes the filter, False otherwise.
            Override this in a subclass.
        """
        return True

    def weight_host(self, host):
        """ Return Weight of host based on his parameter
            Override this in a subclass.
        """
        return 0

    def get_weight(self, host):
        """ Return Weight parameter
            Override this in a subclass.
        """
        return 0

    def filter_all(self, filter_host_list, vm):
        """Returns list of filtered hosts
        """
        filtered = []
        for host in filter_obj_list:
            if self.filter_one(host = host, vm = vm):
                filtered.append(host)
