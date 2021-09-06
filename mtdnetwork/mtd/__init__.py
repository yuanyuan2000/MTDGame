import random
import networkx as nx
import logging
import mtdnetwork.host as host
import mtdnetwork.network as network
import mtdnetwork.constants as constants

class MTD:
    def __init__(self, network):
        self.network = network

    def mtd_operation(self):
        raise NotImplementedError