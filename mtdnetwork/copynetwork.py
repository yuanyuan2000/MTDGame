from mtdnetwork.actions import ActionManager
import networkx as nx
import pkg_resources
import matplotlib.pyplot as plt
import numpy as np
import random
import mtdnetwork.constants as constants
import mtdnetwork.services as services
from mtdnetwork.host import Host
import mtdnetwork.exceptions as exceptions
from mtdnetwork.scorer import Scorer

class Network:

    def __init__(self, graph, pos, colour_map, total_nodes, total_endpoints, total_subnets, total_layers):
        """
        Initialises the state of the network for the simulation.

        Parameters:
            total_nodes: 
                the number of the nodes in the network.
            total_endpoints: 
                the number of nodes exposed on the internet (hacker can interact directly with them).
                total_endpoints must be less than total_nodes.
            total_subdnets: 
                how many subnets in the network.
            total_layers:
                how many layers deep from the exposed endpoints the network is.
            user_to_nodes_ratio:
                the percent of users in comparison to hsot machines.
                each node will then be given `int(1/user_to_nodes_ratio)` users each (less users more users on each computer).
            prob_user_reuse_pass:
                the probability that a user has reused their password.
            seed:
                the seed for the random number generator if one needs to be set
        """
        self.total_nodes = total_nodes
        self.total_endpoints = total_endpoints
        self.total_subnets = total_subnets
        self.layers = total_layers
        self.graph = graph.copy()
        self.pos = pos
        self.colour_map = colour_map
        self.exposed_endpoints = [i for i in range(total_endpoints)]
        self.mtd_strategies = []
        self.reachable = []
        self.target_node = -1
        self.action_manager = ActionManager(self)
        self.scorer = Scorer()
        self.scorer.set_initial_statistics(self)

    def get_scorer(self):
        return self.scorer

    def get_statistics(self):
        return self.scorer.get_statistics()

    def get_hosts(self):
        return dict(nx.get_node_attributes(self.graph, "host"))

    def get_subnets(self):
        return dict(nx.get_node_attributes(self.graph, "subnet"))

    def get_layers(self):
        return dict(nx.get_node_attributes(self.graph, "layer"))
    
    def get_total_nodes(self):
        return self.total_nodes

    def get_target_node(self):
        return self.target_node    

    def get_unique_subnets(self):
        subnets = self.get_subnets()
        layers = self.get_layers()

        layer_subnets = {}

        for host_id, subnet_id in subnets.items():
            layer_id = layers[host_id]

            if not layer_id in layer_subnets:
                layer_subnets[layer_id] = {}

            layer_subnets[layer_id][subnet_id] = layer_subnets[layer_id].get(subnet_id, []) + [host_id]

        return layer_subnets

    def get_action_manager(self):
        """
        Returns:
            the ActionManager for the network
        """
        return self.action_manager


    def set_mtd_trigger_time(self, curr_time):
        """
        Sets the time for when the next MTD operation will be triggered.

        Parameters:
            curr_time:
                the time value that the simulation is currently at
        """
        self.trigger_time = curr_time + random.randint(constants.MTD_MIN_TRIGGER_TIME, constants.MTD_MAX_TRIGGER_TIME)

    def register_mtd(self, mtd_strategy):
        """
        Registers a MTD strategy that will reconfigure the Network during the simulation to try and thwart the hacker.

        Paramters:
            mtd_strategy:
                an instance of MTDStrategy that the network will use to reconfigure the network
        """
        if len(self.mtd_strategies) == 0:
            self.set_mtd_trigger_time(0)
        mtd_strat = mtd_strategy(self)
        self.mtd_strategies.append(mtd_strat)
        self.scorer.register_mtd(mtd_strat)

    def step(self, curr_time):
        """
        Checks if a proactive MTD operation is triggered and randomly picks a MTD strategy and runs its operation.

        Paramters:
            curr_time:
                the time value that the simulation is currently at
        """
        if len(self.mtd_strategies) > 0:
            if curr_time >= self.trigger_time:
                mtd_strat = random.choice(self.mtd_strategies)
                mtd_strat.mtd_operation()
                self.set_mtd_trigger_time(curr_time)
                self.scorer.set_last_mtd(mtd_strat)
                self.scorer.add_mtd_event(curr_time)

    def get_hacker_visible_graph(self):
        """
        Returns the Network graph that is visible to the hacker depending on the hosts that have already been compromised

        Parameters:
            compromised_hosts:
                a list of the host IDs that have already been compromised by the hacker
        """
        visible_hosts = []
        for c_host in self.reachable:
            visible_hosts = visible_hosts + list(self.graph.neighbors(c_host))

        visible_hosts = visible_hosts + self.reachable
        visible_hosts = visible_hosts + self.exposed_endpoints

        return self.graph.subgraph(
            list(set(visible_hosts))
        )

    def get_host(self, host_id):
        """
        Gets the Host instance based on the host_id

        Parameters:
            the ID of the Host Instance

        Returns:
            the corresponding Host instance
        """

        return self.graph.nodes.get(host_id, {}).get("host", None)

    def is_compromised(self, compromised_hosts):
        """
        Checks if the Network has been completely compromised.

        Parameters:
            compromised_hosts:
                the list of host IDs that have been compromised by the hacker

        Returns:
            boolean
        """
        return len(compromised_hosts) == self.total_nodes

    def get_path_from_exposed(self, target_node, graph=None):
        """
        Gets the shortest path and distance from the exposed endpoints.

        Can also specify a subgraph to use for finding

        Parameters:
            target_node:
                the target node to reach to

        Returns:
            a tuple where the first element is the shortest path and the second element is the distance
        """
        if graph == None:
            graph = self.graph

        shortest_distance = constants.LARGE_INT
        shortest_path = []

        for ex_node in self.exposed_endpoints:
            try:
                path = nx.shortest_path(graph, ex_node, target_node)
                path_len = len(path)

                if path_len < shortest_distance:
                    shortest_distance = path_len
                    shortest_path = path
            except:
                pass

        # This function is used for sorting so shouldn't raise an exception
        # some MTD cause this exception to be raised.
        #
        # if shortest_distance == constants.LARGE_INT:
        #     raise exceptions.PathToTargetNotFoundError(target_node)

        return shortest_path, shortest_distance
        

    def scan(self, compromised_hosts, stop_attack):
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
    
        scan_time = constants.NETWORK_HOST_DISCOVER_TIME*visible_network.number_of_nodes()

        uncompromised_hosts = []
        # Add every uncompromised host that is reachable and is not an exposed or compromised host 
        for c_host in compromised_hosts:
            uncompromised_hosts = uncompromised_hosts + [
                neighbor
                    for neighbor in self.graph.neighbors(c_host)
                        if not neighbor in compromised_hosts and not neighbor in self.exposed_endpoints \
                            and len(self.get_path_from_exposed(neighbor, graph=visible_network)[0]) > 0
            ]

        # Sorts array based on tag, putting target first
        uncompromised_hosts = sorted(
            uncompromised_hosts,
            key = lambda host_id : self.get_host_id_priority(host_id) + random.random()
        )

        uncompromised_hosts = uncompromised_hosts + [
            ex_node
                for ex_node in self.exposed_endpoints
                    if not ex_node in compromised_hosts
        ]

        discovered_hosts =  [n for n in uncompromised_hosts if n not in stop_attack]

        return self.action_manager.create_action(
            discovered_hosts,
            scan_time,
            check_network_ips = True,
            check_network_paths = True
        )

    def get_shortest_distance_from_exposed_or_pivot(self, host_id, pivot_host_id=-1, graph=None):
        if host_id in self.exposed_endpoints:
            return 0
        if graph == None:
            graph = self.graph
        shortest_distance = self.get_path_from_exposed(host_id, graph=graph)[1]
        if pivot_host_id >= 0:
            try:
                path = nx.shortest_path(graph, host_id, pivot_host_id)
                path_len = len(path)

                if path_len < shortest_distance:
                    shortest_distance = path_len
            except:
                pass

        return shortest_distance

    def sort_by_distance_from_exposed_and_pivot_host(self, host_stack, compromised_hosts, pivot_host_id=-1):
        """
        Sorts the Host Stack by the shortest number of hops to reach the target hosts.

        Parameters:
            host_stack:
                a list of host IDs the attacker wants to attack
            compromised_hosts:
                a list of host IDs the hacker has compromised
            pivot_host_id:
                the ID of the host that is compromised that the hacker is using to pivot from.
                if None then it only sorts by the exposed endpoints
        """

        visible_network = self.get_hacker_visible_graph()

        non_exposed_endpoints = [
            host_id
                for host_id in host_stack
                    if not host_id in self.exposed_endpoints
        ]

        return sorted(
            non_exposed_endpoints,
            key = lambda host_id : self.get_shortest_distance_from_exposed_or_pivot(
                host_id, 
                pivot_host_id=pivot_host_id, 
                graph=visible_network
            ) + random.random()
        ) + [
            host_id
                for host_id in self.exposed_endpoints
                    if host_id in host_stack
        ]

    def get_neighbors(self, host_id):
        """
        Returns the neighbours for a host.

        Parameters:
            host_id:
                the host ID to get the neighbors from

        Returns:
            a list of the neighbors for the host.
        """
        return list(self.graph.neighbors(host_id))

    def draw(self):
        """
        Draws the topology of the network while also highlighting compromised and exposed endpoint nodes.
        """
        plt.figure(1, figsize=(15,12))
        nx.draw(self.graph, pos=self.pos, node_color=self.colour_map, with_labels=True)
        plt.show()

    def draw_hacker_visible(self):
        """
        Draws the network that is visible for the hacker
        """
        subgraph = self.get_hacker_visible_graph()
        
        plt.figure(1, figsize=(15,12))
        nx.draw(subgraph, pos=self.pos, with_labels=True)
        plt.show()

    def draw_compromised(self, compromised_hosts):
        """
        Draws the network of compromised hosts
        """
        subgraph = self.graph.subgraph(compromised_hosts)
        colour_map = []
        c_hosts = sorted(compromised_hosts)
        for node_id in c_hosts:
            if node_id in self.exposed_endpoints:
                colour_map.append("green")
            else:
                colour_map.append("red")
        
        plt.figure(1, figsize=(15,12))
        nx.draw(subgraph, pos=self.pos, node_color=colour_map, with_labels=True)
        plt.show()
    
    def update_reachable_mtd(self):
        """
        Updates the Reachable array with only compromised nodes that are reachable after MTD
        NOTE: Probably can be optimised for speed
        """
        self.reachable = self.exposed_endpoints.copy()
        compromised_neighbour_nodes = []


        # Appends all neighbouring hosts from endpoints
        for endpoint in self.exposed_endpoints:
            visible_hosts = list(self.graph.neighbors(endpoint))
            for host in visible_hosts:
                for c_host in self.compromised_hosts:
                    if host == c_host:
                        compromised_neighbour_nodes.append(host)
                        self.reachable.append(host)
            
        # Checks if neighbouring hosts of compromised node are also compromised, if so add them to the list
        while len(compromised_neighbour_nodes) != 0:
            appended_host = compromised_neighbour_nodes.pop(0)
            visible_hosts = list(self.graph.neighbors(appended_host))
            for host in visible_hosts:
                for c_host in self.compromised_hosts:
                    if host == c_host:
                        if host not in self.reachable:
                            compromised_neighbour_nodes.append(host)
                            self.reachable.append(host)
                        # repeated = False
                        # for reachable in self.reachable:
                        #     if reachable == host:
                        #         repeated = True
                        # if repeated == False:
                        #     compromised_neighbour_nodes.append(host)
                        #     self.reachable.append(host)
                



    def update_reachable_compromise(self, compromised_node_id, compromised_hosts):
        """
        Updates the Reachable with the node_id of the compromised node
        """
        self.reachable.append(compromised_node_id)
        appended_host = compromised_node_id
        self.compromised_hosts = compromised_hosts
        all_reachable_hosts_added = False
        compromised_neighbour_nodes = []
        

        # Checks if neighbouring hosts of compromised node are also compromised, if so add them to the list
        while all_reachable_hosts_added == False:
            visible_hosts = list(self.graph.neighbors(appended_host))
            for host in visible_hosts:
                for c_host in compromised_hosts:
                    if host == c_host:
                        # repeated = False
                        # for reachable in self.reachable:
                        #     if reachable == host:
                        #         repeated = True
                        # if repeated == False:
                        if host not in self.reachable:
                            compromised_neighbour_nodes.append(host)
                            self.reachable.append(host)
                        
            if len(compromised_neighbour_nodes) == 0:
                all_reachable_hosts_added = True
            else:
                appended_host = compromised_neighbour_nodes.pop(0)
