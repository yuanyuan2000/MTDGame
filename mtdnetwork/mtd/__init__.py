from mtdnetwork.irrelevant_stuff.scorer import MTDStatistics
import logging
import random
from mtdnetwork.network import host, services


class MTD:
    def __init__(self, name, network, resource_type, execution_time):
        self.network = network
        self.name = name
        self.resource_type = resource_type
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
