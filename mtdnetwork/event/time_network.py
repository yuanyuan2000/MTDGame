from queue import PriorityQueue
from collections import deque
import random
from mtdnetwork.copynetwork import Network
from mtdnetwork import constants


class TimeNetwork(Network):

    def __init__(self, graph, pos, colour_map, total_nodes, total_endpoints, total_subnets, total_layers,
                 node_per_layer, users_list, users_per_host):
        # default parameters
        # self.mtd_strategy_queue = PriorityQueue()
        self.mtd_strategy_queue = deque()
        self.suspended_queue = deque()
        super().__init__(graph, pos, colour_map, total_nodes, total_endpoints, total_subnets,
                         total_layers, node_per_layer, users_list, users_per_host)

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
        if len(self.suspended_queue) != 0:
            return self.suspended_queue.popleft()
        return self.mtd_strategy_queue.popleft()

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
                if not neighbor in compromised_hosts and not neighbor in self.exposed_endpoints \
                   and len(self.get_path_from_exposed(neighbor, graph=visible_network)[0]) > 0
            ]

        # Add random element from 0 to 1 so the scan does not return the same order of hosts each time for the hacker
        uncompromised_hosts = sorted(
            uncompromised_hosts,
            key=lambda host_id: self.get_path_from_exposed(host_id, graph=visible_network)[1] + random.random()
        )

        uncompromised_hosts = uncompromised_hosts + [
            ex_node
            for ex_node in self.exposed_endpoints
            if not ex_node in compromised_hosts
        ]

        discovered_hosts = [n for n in uncompromised_hosts if n not in stop_attack]

        return discovered_hosts

