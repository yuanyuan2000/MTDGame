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

class AltNetwork:

    def __init__(self, total_nodes, total_endpoints, total_subnets, total_layers,
                    users_to_nodes_ratio=constants.USER_TO_NODES_RATIO, prob_user_reuse_pass=constants.USER_PROB_TO_REUSE_PASS, seed=None):
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
        self.total_subnets = total_subnets
        self.layers = total_layers
        self.exposed_endpoints = [i for i in range(total_endpoints)]
        self.service_generator = services.ServicesGenerator()
        self.mtd_strategies = []
        self.action_manager = ActionManager(self)
        self.scorer = Scorer()
        self.gen_graph()
        self.setup_network()

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


    def setup_users(self, user_to_nodes_ratio, prob_user_reuse_pass, users_per_host):
        """
        Randomly generates users that use the network

        Parameters:
            user_to_nodes_ratio:
                the percent of users in comparison to host machines.
                each node will then be given `int(1/user_to_nodes_ratio)` users each (less users more users on each computer).
            prob_user_reuse_pass:
                the probability that a user has reused their password.
            users_per_host:
                how many users are allocated to each host on the network.
        """
        self.total_users = int(self.total_nodes*user_to_nodes_ratio)
        if self.total_users < 1:
            self.total_users = 1
        
        names = [x.decode() for x in pkg_resources.resource_string('mtdnetwork', "data/first-names.txt").splitlines()]

        random_users = random.choices(names, k=self.total_users)
        self.users_list = [
            (user, random.random() < prob_user_reuse_pass)
                for user in random_users
        ]
        
        self.users_per_host = users_per_host    
    def draw(self):
        """
        Draws the topology of the network while also highlighting compromised and exposed endpoint nodes.
        """
        plt.figure(1, figsize=(15,12))
        nx.draw(self.graph, with_labels=True)
        plt.show()

    def gen_graph(self, min_nodes_per_subnet=3, max_subnets_per_layer=5, subnet_m_ratio=0.2, 
                    prob_inter_layer_edge=0.4):
        # self.graphenerate the graph
        self.graph = nx.Graph()
        subgraph = nx.barabasi_albert_graph(10, 2)
        self.graph = nx.compose(self.graph, subgraph)




 
