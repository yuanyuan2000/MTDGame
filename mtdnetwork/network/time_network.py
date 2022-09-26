import random
from collections import deque
from mtdnetwork.network.copynetwork import Network
from mtdnetwork.stats.mtd_stats import MTDStatistics
from mtdnetwork.network.mtd_schedule import MTDSchedule
from mtdnetwork.network.targetnetwork import TargetNetwork


class TimeNetwork(Network):

    def __init__(self, graph, pos, colour_map, total_nodes, total_endpoints, total_subnets, total_layers,
                 node_per_layer, users_list, users_per_host):
        # default parameters
        # self.mtd_strategy_queue = PriorityQueue()
        self._mtd_stats = MTDStatistics()
        self._mtd_schedule = MTDSchedule(network=self)
        self._mtd_strategy_queue = deque()
        self._mtd_suspended_queue = deque()
        self._unfinished_mtd = None
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

    def initialise_mtd_schedule(self, mtd_interval_schedule, mtd_strategy_schedule,
                                timestamps=None, compromised_ratios=None):
        self._mtd_schedule.set_mtd_interval_schedule(mtd_interval_schedule)
        self._mtd_schedule.set_mtd_strategy_schedule(mtd_strategy_schedule)
        self._mtd_schedule.set_timestamps(timestamps)
        self._mtd_schedule.set_compromised_ratios(compromised_ratios)
        self._mtd_stats.append_mtd_interval_record(0, mtd_interval_schedule)
        self._mtd_stats.append_mtd_strategy_record(0, 'diversity')

    def host_scan(self, compromised_hosts, stop_attack):
        """
        Scans the network and returns a sorted list of discovered hosts that have not been compromised yet.

        The uncompromised hosts will be sorted by distance from the exposed endpoints, which the Hacker will prefer
        since it would be easier to reach closer nodes than ones further away.

        However, nodes that are not exposed will be preferred by the hacker since they offer a much higher likelihood
        of compromising more hosts.

        Parameters:
            compromised_hosts:
                a list of host IDs that have been compromised
            stop_attack:
                a list of host IDs which have reached attack threshold and can't be attacked anymore

        Returns:
            an action that will return the scanned hosts if not blocked by a MTD
        """

        visible_network = self.get_hacker_visible_graph()
        # scan_time = constants.NETWORK_HOST_DISCOVER_TIME * visible_network.number_of_nodes()
        uncompromised_hosts = []
        # Add every uncompromised host that is reachable and is not an exposed or compromised host
        for c_host in compromised_hosts:
            uncompromised_hosts = uncompromised_hosts + [
                neighbor
                for neighbor in self.graph.neighbors(c_host)
                if neighbor not in compromised_hosts and neighbor not in self.exposed_endpoints and
                   len(self.get_path_from_exposed(neighbor, graph=visible_network)[0]) > 0
            ]

        # Add random element from 0 to 1 so the scan does not return the same order of hosts each time for the hacker
        uncompromised_hosts = sorted(
            uncompromised_hosts,
            key=lambda host_id: self.get_path_from_exposed(host_id, graph=visible_network)[1] + random.random()
        )

        uncompromised_hosts = uncompromised_hosts + [
            ex_node
            for ex_node in self.exposed_endpoints
            if ex_node not in compromised_hosts
        ]

        discovered_hosts = [n for n in uncompromised_hosts if n not in stop_attack]

        return discovered_hosts

    def compromised_ratio(self, compromised_hosts):
        return compromised_hosts / self.total_nodes

    def get_mtd_schedule(self):
        return self._mtd_schedule

    def get_mtd_stats(self):
        return self._mtd_stats

    def get_mtd_strategy_queue(self):
        return self._mtd_strategy_queue

    def get_mtd_suspended_queue(self):
        return self._mtd_suspended_queue

    def get_unfinished_mtd(self):
        return self._unfinished_mtd

    def set_unfinished_mtd(self, mtd):
        self._unfinished_mtd = mtd
