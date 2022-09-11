import logging
import random
from mtdnetwork.network import host, services


class MTD:
    def __init__(self, name, network, resource_type, resource, execution_time_mean, execution_time_std):
        self.network = network
        self.name = name
        self.resource_type = resource_type
        self.resource = resource
        self.execution_time_mean = execution_time_mean
        self.execution_time_std = execution_time_std

    def mtd_operation(self, adversary=None):
        raise NotImplementedError

    def __str__(self):
        return self.name + ' ' + self.resource_type + ' ' + self.execution_time_mean


