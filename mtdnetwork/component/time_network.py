from mtdnetwork.component.copynetwork import Network
from mtdnetwork.statistic.mtd_statistics import MTDStatistics
from mtdnetwork.component.targetnetwork import TargetNetwork


class TimeNetwork(Network):

    def __init__(self, graph, pos, colour_map, total_nodes, total_endpoints, total_subnets, total_layers,
                 node_per_layer, users_list, users_per_host):
        # default parameters
        self._mtd_stats = MTDStatistics()
        self._mtd_queue = []
        self._suspended_mtd = dict()
        self._unfinished_mtd = dict()
        super().__init__(graph, pos, colour_map, total_nodes, total_endpoints, total_subnets,
                         total_layers, node_per_layer, users_list, users_per_host)

    @staticmethod
    def create_network():
        target_network = TargetNetwork(total_nodes=200, total_endpoints=20, total_subnets=20, total_layers=5,
                                       target_layer=2)
        graph = target_network.get_graph_copy()
        colour_map = target_network.get_colourmap()
        pos = target_network.get_pos()
        node_per_layer = target_network.get_node_per_layer()
        users_list = target_network.get_users_list()
        users_per_host = target_network.get_users_per_host()
        time_network = TimeNetwork(graph, pos, colour_map, 200, 20, 20, 5, node_per_layer, users_list,
                                   users_per_host)
        return time_network

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
