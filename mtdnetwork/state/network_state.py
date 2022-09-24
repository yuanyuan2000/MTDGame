import pickle
from mtdnetwork.state import State
from mtdnetwork.network.time_network import TimeNetwork
from mtdnetwork.network.host import Host
from mtdnetwork.network.services import Service


class NetworkState(State):
    def __init__(self):
        super().__init__()

    def save_network_state(self, network: TimeNetwork, timestamp: float):
        """saving data related to generate the network graph"""
        network = network.clear_properties()
        file_name = self.save_file_by_time('network', timestamp)
        with open(file_name, 'wb') as f:
            pickle.dump(network, f, pickle.HIGHEST_PROTOCOL)

    def load_network_state(self, timestamp):
        """saving data related to generate the network graph"""
        if timestamp == 0:
            return
        file_name = self.save_file_by_time('network', timestamp)
        with open(file_name, 'rb') as f:
            network = pickle.load(f)
            return network

    # def save_host_state(self, host: Host):
    #     # todo: saving data related to generate a host in the network
    #     pass
    #
    # def save_service_state(self, service: Service):
    #     # todo: saving data related to generate a service in a host
    #     pass

    # def load_host_state(self, host: Host):
    #     # todo: saving data related to generate a host in the network
    #     pass
    #
    # def load_service_state(self, service: Service):
    #     # todo: saving data related to generate a service in a host
    #     pass
