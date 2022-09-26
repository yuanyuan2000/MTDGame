import logging
import random
from mtdnetwork.network import host, services


class MTD:
    def __init__(self, name, network, resource_type, execution_time_mean, execution_time_std):
        self.network = network
        self.name = name
        self.resource_type = resource_type
        self.execution_time_mean = execution_time_mean
        self.execution_time_std = execution_time_std

    def mtd_operation(self, adversary=None):
        raise NotImplementedError

    def __str__(self):
        return self.name + ' ' + self.resource_type + ' ' + self.execution_time_mean

    def get_resource_type(self):
        return self.resource_type

    def get_name(self):
        return self.name

    def get_execution_time_mean(self):
        return self.execution_time_mean

    def get_execution_time_std(self):
        return self.execution_time_std
