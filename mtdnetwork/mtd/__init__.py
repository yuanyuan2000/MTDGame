import random
import networkx as nx
import logging
import mtdnetwork.host as host
import mtdnetwork.targetnetwork as targetnetwork
import mtdnetwork.constants as constants
from mtdnetwork.scorer import MTDStatistics

class MTD:
    def __init__(self, name, network, resource, execution_time):
        self.network = network
        self.name = name
        self.resource = resource
        self.execution_time = execution_time
        self.record = MTDStatistics(self.name)

    def mtd_operation(self):
        raise NotImplementedError

    def add_trigger_event(self, curr_time):
        # Only adding 1 as the value since we already know what MTD strategy was triggered
        self.record.add_event(curr_time, 1)

    def __str__(self):
        return self.name

    def get_record(self):
        return self.record