from collections import deque
import random
from mtdnetwork.network.copynetwork import Network
import simpy
from mtdnetwork.stats.mtd_stats import MTDStatistics
from mtdnetwork.event.mtd_schedule import MTDSchedule
from mtdnetwork.network.targetnetwork import TargetNetwork


class TimeNetwork(Network):

    def __init__(self, env, graph, pos, colour_map, total_nodes, total_endpoints, total_subnets, total_layers,
                 node_per_layer, users_list, users_per_host):
        # default parameters
        # self.mtd_strategy_queue = PriorityQueue()
        self.env = env
        self.now = 0
        self.mtd_strategy_queue = deque()
        self.suspended_queue = deque()
        self.application_layer_resource = simpy.Resource(self.env, 1)
        self.network_layer_resource = simpy.Resource(self.env, 1)
        self.reserve_resource = simpy.Resource(self.env, 1)
        self.mtd_stats = MTDStatistics()
        self.mtd_schedule = MTDSchedule(network=self)
        super().__init__(graph, pos, colour_map, total_nodes, total_endpoints, total_subnets,
                         total_layers, node_per_layer, users_list, users_per_host)

    @staticmethod
    def create_network(env):
        target_network = TargetNetwork(total_nodes=200, total_endpoints=20, total_subnets=20, total_layers=5,
                                       target_layer=2)
        graph = target_network.get_graph_copy()
        colour_map = target_network.get_colourmap()
        pos = target_network.get_pos()
        node_per_layer = target_network.get_node_per_layer()
        users_list = target_network.get_users_list()
        users_per_host = target_network.get_users_per_host()
        time_network = TimeNetwork(env, graph, pos, colour_map, 200, 20, 20, 5, node_per_layer, users_list,
                                   users_per_host)
        return time_network

    def initialise_mtd_schedule(self, mtd_interval_schedule, mtd_strategy_schedule,
                                timestamps=None, compromised_ratios=None):
        self.mtd_schedule.set_mtd_interval_schedule(mtd_interval_schedule)
        self.mtd_schedule.set_mtd_strategy_schedule(mtd_strategy_schedule)
        self.mtd_schedule.set_timestamps(timestamps)
        self.mtd_schedule.set_compromised_ratios(compromised_ratios)
        self.mtd_stats.append_mtd_interval_record(0, mtd_interval_schedule)
        self.mtd_stats.append_mtd_strategy_record(0, 'diversity')

    def register_mtd(self, mtd_strategy):
        """
        Registers an MTD strategy that will reconfigure the Network during the simulation to try and thwart the hacker.

        Paramters:
            mtd_strategy:
                an instance of MTDStrategy that the network will use to reconfigure the network
        """
        mtd_strategy = mtd_strategy(self)
        self.mtd_strategy_queue.append(mtd_strategy)

    def trigger_mtd(self):
        """
        pop up the MTD and trigger it.
        :return:
        """
        self.mtd_stats.total_triggered += 1
        if len(self.suspended_queue) != 0:
            return self.suspended_queue.popleft()
        return self.mtd_strategy_queue.popleft()

    def suspend_mtd(self, mtd_strategy):
        self.mtd_stats.total_suspended += 1
        self.suspended_queue.append(mtd_strategy)

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

    def reconfigure_network(self):
        pass

    def compromised_ratio(self, compromised_hosts):
        return compromised_hosts / self.total_nodes

    def get_mtd_schedule(self):
        return self.mtd_schedule

    def get_mtd_stats(self):
        return self.mtd_stats

    def clear_properties(self):
        self.reserve_resource = None
        self.application_layer_resource = None
        self.network_layer_resource = None
        self.env = None
        self.mtd_strategy_queue = deque()
        self.suspended_queue = deque()
        return self

    def reconfigure_properties(self, env, now):
        self.env = env
        self.now = now
        self.application_layer_resource = simpy.Resource(self.env, 1)
        self.network_layer_resource = simpy.Resource(self.env, 1)
        self.reserve_resource = simpy.Resource(self.env, 1)

