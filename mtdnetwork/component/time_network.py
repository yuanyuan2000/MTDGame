from mtdnetwork.component.network import Network
from mtdnetwork.statistic.mtd_statistics import MTDStatistics


class TimeNetwork(Network):

    def __init__(self, total_nodes=200, total_endpoints=20, total_subnets=20, total_layers=5, target_layer=2):
        # default parameters
        self._mtd_stats = MTDStatistics()
        self._mtd_queue = []
        self._suspended_mtd = dict()
        self._unfinished_mtd = dict()
        super().__init__(total_nodes=total_nodes, total_endpoints=total_endpoints, total_subnets=total_subnets,
                         total_layers=total_layers, target_layer=target_layer)
        self.init_network()

    def is_compromised(self, compromised_hosts):
        # TODO: refactor terminating condition
        super().is_compromised(compromised_hosts)
        pass

    def get_mtd_stats(self):
        return self._mtd_stats

    def get_mtd_queue(self):
        return self._mtd_queue

    def get_suspended_mtd(self):
        return self._suspended_mtd

    def get_unfinished_mtd(self):
        return self._unfinished_mtd

    def set_unfinished_mtd(self, mtd):
        self._unfinished_mtd[mtd.get_resource_type()] = mtd
