import pickle
from mtdnetwork.snapshot import Snapshot
from mtdnetwork.network.time_network import TimeNetwork


class NetworkSnapshot(Snapshot):
    def __init__(self):
        super().__init__()

    def save_network(self, network: TimeNetwork, timestamp: float):
        """saving data related to generate the network graph"""
        file_name = self.get_file_by_time('network', timestamp)
        with open(file_name, 'wb') as f:
            pickle.dump(network, f, pickle.HIGHEST_PROTOCOL)

    def load_network(self, timestamp):
        """loading data related to generate the network graph"""
        if timestamp == 0:
            return
        file_name = self.get_file_by_time('network', timestamp)
        with open(file_name, 'rb') as f:
            network = pickle.load(f)
            return network
