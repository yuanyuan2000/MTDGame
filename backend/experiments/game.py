import os
import sys
current_directory = os.getcwd()
experimental_path = os.path.join(current_directory, 'experiments')
experimental_data_path = os.path.join(experimental_path, 'experimental_data')
if not os.path.exists(experimental_data_path):
    os.makedirs(experimental_data_path)
    plots_path = os.path.join(experimental_data_path, 'plots')
    os.makedirs(plots_path)
    results_path = os.path.join(experimental_data_path, 'results')
    os.makedirs(results_path)
sys.path.append(current_directory.replace('experiments', ''))
import warnings
warnings.filterwarnings("ignore")
import matplotlib.pyplot as plt
plt.set_loglevel('WARNING')
import logging
logging.basicConfig(format='%(message)s', level=logging.INFO)

import simpy
import pandas as pd
from mtdnetwork.component.time_network import TimeNetwork
from mtdnetwork.operation.mtd_operation import MTDOperation
from mtdnetwork.data.constants import ATTACKER_THRESHOLD, OS_TYPES
from mtdnetwork.component.adversary import Adversary
from mtdnetwork.operation.attack_operation import AttackOperation
from mtdnetwork.snapshot.snapshot_checkpoint import SnapshotCheckpoint
from mtdnetwork.statistic.evaluation import Evaluation
from mtdnetwork.mtd.completetopologyshuffle import CompleteTopologyShuffle
from mtdnetwork.mtd.ipshuffle import IPShuffle
from mtdnetwork.mtd.hosttopologyshuffle import HostTopologyShuffle
from mtdnetwork.mtd.portshuffle import PortShuffle
from mtdnetwork.mtd.osdiversity import OSDiversity
from mtdnetwork.mtd.servicediversity import ServiceDiversity
from mtdnetwork.mtd.usershuffle import UserShuffle
from mtdnetwork.mtd.osdiversityassignment import OSDiversityAssignment
import random
import threading
import queue

# Constants for game
WIDTH = 1600
HEIGHT = 900
BLANK = 50
NODE_RADIUS = 12
EDGE_WIDTH = 1

# def create_experiment_snapshots(network_size_list):
#     snapshot_checkpoint = SnapshotCheckpoint()
#     for size in network_size_list:
#         time_network = TimeNetwork(total_nodes=size)
#         adversary = Adversary(network=time_network, attack_threshold=ATTACKER_THRESHOLD)
#         snapshot_checkpoint.save_snapshots_by_network_size(time_network, adversary)

class Node:

    def __init__(self, num, x, y, color):
        self.id = num
        self.x = x
        self.y = y
        self.color = color

        self.is_chosen = False  # whether the node is chosen by users

class Game:
    def __init__(self) -> None:
        self.width = WIDTH
        self.height = HEIGHT

        self.env = simpy.Environment()
        self.snapshot_checkpoint = None
        self.time_network = None
        self.adversary = None
        self.attack_operation = None
        self.mtd_operation = None
        self.evaluation = None
        self.nodes = []

    def get_env(self):
        return self.env
    
    def get_snapshot_checkpoint(self):
        return self.snapshot_checkpoint
    
    def get_time_network(self):
        return self.time_network
    
    def get_adversary(self):
        return self.adversary
    
    def get_attack_operation(self):
        return self.attack_operation
    
    def get_mtd_operation(self):
        return self.mtd_operation
    
    def get_evaluation(self):
        return self.evaluation
    
    def get_nodes(self):
        return self.nodes
    
    def get_edges(self):
        edges = self.time_network.graph.edges
        # from pprint import pprint
        # def serialize_edges(edges):
        #     serialize_edges = []
        #     for edge in edges:
        #         serialize_edges.append(vars(edge))
        #     return serialize_edges
        # pprint(edges)
        return edges
    
    def update_network(self):
        """
        update the information about the network and the nodes in network
        """
        self.scale_x = 140
        self.scale_y = (self.height - BLANK * 2) // (self.time_network.max_y_pos - self.time_network.min_y_pos)
        self.shift_y = self.height - BLANK * 2 - self.scale_y * self.time_network.max_y_pos

        pos_dict = self.time_network.pos
        color_list = self.time_network.colour_map
        self.nodes = []
        for key, color in zip(pos_dict, color_list):
            x = (pos_dict[key][0] * self.scale_x) + BLANK
            y = (pos_dict[key][1] * self.scale_y) + self.shift_y + BLANK
            self.nodes.append(Node(key, x, y, color))

    
    def execute_simulation(self, start_time=0, finish_time=None, scheme='random', mtd_interval=None, custom_strategies=None,
                        checkpoints=None, total_nodes=50, total_endpoints=5, total_subnets=8, total_layers=4,
                        target_layer=4, total_database=2, terminate_compromise_ratio=0.8, new_network=False):
        """

        :param start_time: the time to start the simulation, need to load timestamp-based snapshots if set start_time > 0
        :param finish_time: the time to finish the simulation. Set to None will run the simulation until
        the network reached compromised threshold (compromise ratio > 0.9)
        :param scheme: random, simultaneous, alternative, single, None
        :param mtd_interval: the time interval to trigger an MTD(s)
        :param custom_strategies: used for executing alternative scheme or single mtd strategy.
        :param checkpoints: a list of time value to save snapshots as the simulation runs.
        :param total_nodes: the number of nodes in the network (network size)
        :param total_endpoints: the number of exposed nodes
        :param total_subnets: the number of subnets (total_nodes - total_endpoints) / (total_subnets - 1) > 2
        :param total_layers: the number of layers in the network
        :param target_layer: the target layer in the network (for targetted attack scenario only)
        :param total_database: the number of database nodes used for computing DAP algorithm
        :param terminate_compromise_ratio: terminate the simulation if reached compromise ratio
        :param new_network: True: create new snapshots based on network size, False: load snapshots based on network size
        """
        
        end_event = self.env.event()
        self.snapshot_checkpoint = SnapshotCheckpoint(env=self.env, checkpoints=checkpoints)
        

        if start_time > 0:
            try:
                self.time_network, self.adversary = self.snapshot_checkpoint.load_snapshots_by_time(start_time)
            except FileNotFoundError:
                print('No timestamp-based snapshots available! Set start_time = 0 !')
                return
        elif not new_network:
            try:
                self.time_network, self.adversary = self.snapshot_checkpoint.load_snapshots_by_network_size(total_nodes)
            except FileNotFoundError:
                print('set new_network=True')
        else:
            self.time_network = TimeNetwork(total_nodes=total_nodes, total_endpoints=total_endpoints,
                                    total_subnets=total_subnets, total_layers=total_layers,
                                    target_layer=target_layer, total_database=total_database,
                                    terminate_compromise_ratio=terminate_compromise_ratio)
            self.adversary = Adversary(network=self.time_network, attack_threshold=ATTACKER_THRESHOLD)
            self.snapshot_checkpoint.save_snapshots_by_network_size(self.time_network, self.adversary)

        # update network information
        self.update_network()
        
        # from pprint import pprint
        # def serialize_nodes(nodes):
        #     serialized_nodes = []
        #     for node in nodes:
        #         serialized_nodes.append(vars(node))
        #     return serialized_nodes
        # pprint(serialize_nodes(self.nodes))


        # start attack
        self.attack_operation = AttackOperation(env=self.env, end_event=end_event, adversary=self.adversary, proceed_time=0)
        self.attack_operation.proceed_attack()

        # start mtd
        if scheme != 'None':
            self.mtd_operation = MTDOperation(env=self.env, end_event=end_event, network=self.time_network, scheme=scheme,
                                        attack_operation=self.attack_operation, proceed_time=0,
                                        mtd_trigger_interval=mtd_interval, custom_strategies=custom_strategies)
            self.mtd_operation.proceed_mtd()

        # save snapshot by time
        if checkpoints is not None:
            self.snapshot_checkpoint.proceed_save(self.time_network, self.adversary)

        # start simulation
        if finish_time is not None:
            self.env.run(until=(finish_time - start_time))
        else:
            self.env.run(until=end_event)

        self.evaluation = Evaluation(network=self.time_network, adversary=self.adversary)


    def start(self):

        # create_experiment_snapshots([25, 50, 75, 100])

        self.execute_simulation(start_time=0, finish_time=3000, mtd_interval=200, scheme='random', total_nodes=64, new_network=True)