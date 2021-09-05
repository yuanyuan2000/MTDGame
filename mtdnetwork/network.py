from mtdnetwork.actions import ActionManager
import networkx as nx
import importlib.resources as pkg_resources
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import random
import os
import mtdnetwork.constants as constants
import mtdnetwork.services as services
from mtdnetwork.host import Host
import mtdnetwork.data as simdata
import mtdnetwork.exceptions as exceptions

class Network:

    def __init__(self, total_nodes, total_endpoints, total_subnets, total_layers,
                    users_to_nodes_ratio=1/3, prob_user_reuse_pass=0.05, seed=None):
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
        if seed != None:
            random.seed(seed)
        self.total_nodes = total_nodes
        self.total_endpoints = total_endpoints
        self.exposed_endpoints = [i for i in range(total_endpoints)]
        self.service_generator = services.ServicesGenerator()
        self.mtd_strategies = []
        self.action_manager = ActionManager(self)
        self.setup_users(users_to_nodes_ratio, prob_user_reuse_pass, int(1/users_to_nodes_ratio))
        self.gen_graph(total_subnets = total_subnets, layers = total_layers)
        self.setup_network()

    def get_action_manager(self):
        """
        Returns:
            the ActionManager for the network
        """
        return self.action_manager

    def setup_users(self, user_to_nodes_ratio, prob_user_reuse_pass, users_per_host):
        """
        Randomly generates users that use the network

        Parameters:
            user_to_nodes_ratio:
                the percent of users in comparison to hsot machines.
                each node will then be given `int(1/user_to_nodes_ratio)` users each (less users more users on each computer).
            prob_user_reuse_pass:
                the probability that a user has reused their password.
            users_per_host:
                how many users are allocated to each host on the network.
        """
        self.total_users = int(self.total_nodes*user_to_nodes_ratio)
        if self.total_users < 1:
            self.total_users = 1
        
        names = pkg_resources.read_text(simdata, "first-names.txt").splitlines()

        random_users = random.choices(names, k=self.total_users)
        self.users_list = [
            (user, random.random() < prob_user_reuse_pass)
                for user in random_users
        ]
        
        self.users_per_host = users_per_host

    def gen_graph(self, min_nodes_per_subnet=3, total_subnets=10, 
                    max_subnets_per_layer=5, subnet_m_ratio=0.2, prob_inter_layer_edge=0.4, layers=3):
        """
        Generates a network of subnets using the Barabasi-Albert Random Graph model.

        Parameters:
            min_nodes_per_subnet:
                minimum number of computer nodes for each subnet
            total_subnets:
                total subnets in the network.
            max_subnets_per_layer:
                the maximum number of subnets per layer
            subnet_m_ratio:
                a ratio that is used to determine the parameter m for the barabasi albert graph.
                m is the number of edges to attach from a new node to existing nodes
            prob_inter_layer_edge:
                probability that a node connects to a different layer in the network.
            layers:
                how many layers from the exposed endpoints there should be
        """
        # Decide the number of subnets for each layer of the network
        subnets_per_layer = []
        while len(subnets_per_layer) < layers:
            if len(subnets_per_layer) == 0: subnets_per_layer.append(1)
            l_subnets = random.randint(1, max_subnets_per_layer)
            if total_subnets - (sum(subnets_per_layer) + l_subnets) > layers - len(subnets_per_layer):
                subnets_per_layer.append(l_subnets)
        
        while sum(subnets_per_layer) < total_subnets:
            s_index = random.randint(1,layers-1)
            subnets_per_layer[s_index] = subnets_per_layer[s_index] + 1
        
        max_subnet_in_layer = max(subnets_per_layer)
        
        # Assign nodes to each layer
        nodes_per_layer = [self.total_endpoints]
        for subs in subnets_per_layer[1:]:
            nodes_per_layer.append(min_nodes_per_subnet*subs)
            
        while sum(nodes_per_layer) < self.total_nodes:
            n_index = random.randint(1,layers-1)
            nodes_per_layer[n_index] = nodes_per_layer[n_index] + 1
            
        # Assign nodes to each subnet
        subnet_nodes = []
        for i,subnets in enumerate(subnets_per_layer):
            temp_subnet_nodes = [min_nodes_per_subnet for _i in range(subnets)]
            while sum(temp_subnet_nodes) < nodes_per_layer[i]:
                n_index = random.randint(0, subnets-1)
                temp_subnet_nodes[n_index] = temp_subnet_nodes[n_index] + 1
            subnet_nodes.append(temp_subnet_nodes)
            

        
        # self.graphenerate the graph
        self.graph = nx.Graph()
        node_id = 0
        self.colour_map = []
        self.pos = {}
        attr = {}
        min_y_pos = 200000
        max_y_pos = -200000
        for i, subnet_node_list in enumerate(subnet_nodes):
            for j,s_nodes in enumerate(subnet_node_list):
                m = int(s_nodes*subnet_m_ratio)
                if m < 1: m = 1
                elif m >= s_nodes: m = s_nodes - 1
                subgraph = nx.barabasi_albert_graph(s_nodes, m)
                new_node_mapping = {k:k+node_id for k in range(s_nodes)}
                subgraph = nx.relabel_nodes(subgraph, new_node_mapping)
                new_attr = {k+node_id:{"subnet":j,"layer":i} for k in range(s_nodes)}
                attr = {**attr, **new_attr}
                
                node_id += s_nodes

                subgraph_pos = nx.spring_layout(subgraph)
                if i != 0:
                    subgraph_pos = {
                        k:np.array([v[0]+i*2.25, v[1]+j*3 + 1.5*(max_subnet_in_layer - len(subnet_node_list))]) 
                            for k,v in subgraph_pos.items()
                    }
                    
                    for k,v in subgraph_pos.items():
                        y = v[1]+j*3 + 1.5*(max_subnet_in_layer - len(subnet_node_list))
                        subgraph_pos[k] = np.array(
                            [v[0]+i*2.25, y]
                        )
                        if y < min_y_pos:
                            min_y_pos = y
                        if y > max_y_pos:
                            max_y_pos = y
                else:
                    subgraph_pos = {
                        k:np.array([0, k]) 
                            for k,_v in subgraph_pos.items()
                    }
                self.pos = {**self.pos, **subgraph_pos}
                for k in range(s_nodes):
                    if i == 0:
                        self.colour_map.append("green")
                    else:
                        self.colour_map.append("blue")
                        
                self.graph = nx.compose(self.graph, subgraph)
        
        nx.set_node_attributes(self.graph, attr)
        
        # Connect the graph
        def get_other_node(node_list, node_degrees, other_node):
            n = random.choices(node_list, weights=node_degrees, k=1)[0]
            if n == other_node:
                return get_other_node(node_list, node_degrees, other_node)
            return n
        
        while not nx.is_connected(self.graph):
            node_layers = nx.get_node_attributes(self.graph, "layer")
            for i in range(layers-1):
                node_a = [n for n in node_layers if node_layers[n] == i]
                degree_node_a = [self.graph.degree(n) for n in node_a]
                node_b = [n for n in node_layers if node_layers[n] == i+1]
                degree_node_b = [self.graph.degree(n) for n in node_b]
                
                n_a1 = random.choices(node_a, weights=degree_node_a, k=1)[0]
                if not nx.is_connected(self.graph.subgraph(node_a + node_b)):
                    n_b = random.choices(node_b, weights=degree_node_b, k=1)[0]
                    self.graph.add_edge(n_a1, n_b)
                if random.random() < prob_inter_layer_edge and subnets_per_layer[i] > 1 and not nx.is_connected(self.graph.subgraph(node_a)):
                    n_a2 = get_other_node(node_a, degree_node_a, n_a1)
                    self.graph.add_edge(n_a1, n_a2)
                
        # Remove edges between endpoint nodes (not needed since adversary can reach them all anyway)
        # Also fix positions for endpoints
        endpoint_nodes_list = [n for n in range(self.total_endpoints)]
        for n in endpoint_nodes_list:
            self.pos[n] = np.array([0, (n+1)/self.total_endpoints*(max_y_pos - min_y_pos) + min_y_pos])
            neighbors = list(self.graph.neighbors(n))
            for neighbor in neighbors:
                if neighbor in endpoint_nodes_list:
                    self.graph.remove_edge(n, neighbor)

    def setup_network(self):
        """
        Using the generated graph, generates a host for each node on the graph.
        """
        ip_addresses = []
        for host_id in range(self.total_nodes):
            node_os = Host.get_random_os()
            node_os_version = Host.get_random_os_version(node_os)
            node_ip = Host.get_random_address(existing_addresses=ip_addresses)
            ip_addresses.append(node_ip)
            self.graph.nodes[host_id]["host"] = Host(
                node_os,
                node_os_version,
                host_id,
                node_ip,
                random.choices(self.users_list, k=self.users_per_host),
                self,
                self.service_generator,
                self.action_manager
            )

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
        self.mtd_strategies.append(mtd_strategy(self))

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

    def get_hacker_visible_graph(self, compromised_hosts):
        """
        Returns the Network graph that is visible to the hacker depending on the hosts that have already been compromised

        Parameters:
            compromised_hosts:
                a list of the host IDs that have already been compromised by the hacker
        """
        visible_hosts = []
        for c_host in compromised_hosts:
            visible_hosts = visible_hosts + list(self.graph.neighbors(c_host))

        visible_hosts = visible_hosts + compromised_hosts
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

        if shortest_distance == constants.LARGE_INT:
            raise exceptions.PathToTargetNotFoundError

        return shortest_path, shortest_distance
        

    def scan(self, compromised_hosts):
        """
        Scans the network and returns a sorted list of discovered hosts that have not been compromised yet.

        The uncompromised hosts will be sorted by distance from the exposed endpoints, which the Hacker will prefer
        since it would be easier to reach closer nodes than ones further away.

        However, nodes that are not exposed will be preferred by the hacker since they offer a much higher likelihood
        of compromising more hosts.

        Parameters:
            compromised_hosts:
                a list of host IDs that have been compromised

        Returns:
            an action that will return the scanned hosts if not blocked by a MTD
        """

        visible_network = self.get_hacker_visible_graph(compromised_hosts)
    
        scan_time = constants.NETWORK_HOST_DISCOVER_TIME*visible_network.number_of_nodes()

        uncompromised_hosts = []
        for c_host in compromised_hosts:
            uncompromised_hosts = uncompromised_hosts + [
                neighbor
                    for neighbor in self.graph.neighbors(c_host)
                        if not neighbor in compromised_hosts and not neighbor in self.exposed_endpoints
            ]

        uncompromised_hosts = sorted(
            uncompromised_hosts,
            key = lambda host_id : self.get_path_from_exposed(host_id, graph=visible_network)[1]
        )

        uncompromised_hosts = uncompromised_hosts + [
            ex_node
                for ex_node in self.exposed_endpoints
                    if not ex_node in compromised_hosts
        ]

        return self.action_manager.create_action(
            uncompromised_hosts,
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

        visible_network = self.get_hacker_visible_graph(compromised_hosts)

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
            )
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

    def draw_hacker_visible(self, compromised_hosts):
        """
        Draws the network that is visible for the hacker
        """
        subgraph = self.get_hacker_visible_graph(compromised_hosts)
        
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