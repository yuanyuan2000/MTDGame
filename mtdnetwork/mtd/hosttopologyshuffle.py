from mtdnetwork.mtd import *

class HostTopologyShuffle(MTD):
    """
    Swaps hosts in the network.
    """

    def __init__(self, network):
        self.logger = logging.getLogger("mtd:hostshuffle")
        super().__init__("HostTopologyShuffle", network)

    def random_different_host_id(self, curr_host_id, hosts_list):
        other_host_id = random.choice(hosts_list)
        if other_host_id == curr_host_id:
            return self.random_different_host_id(curr_host_id, hosts_list)
        return other_host_id

    def mtd_operation(self):
        self.logger.info("swapping hosts")
        hosts = self.network.get_hosts()
        host_id_list = list(hosts.keys())
        hacker = self.network.get_action_manager().get_hacker()
        exposed_endpoints = self.network.exposed_endpoints
        seen = []

        for host_id, host_instance in hosts.items():
            if host_id in seen or host_id in exposed_endpoints:
                continue
            other_host_id = self.random_different_host_id(host_id, host_id_list)
            if other_host_id in seen or host_id in exposed_endpoints:
                continue
            other_host_instance = hosts[other_host_id]

            host_instance.host_id = other_host_id
            other_host_instance.host_id = host_id

            self.network.graph.nodes[host_id]["host"] = other_host_instance
            self.network.graph.nodes[other_host_id]["host"] = host_instance

            seen.append(host_id)
            seen.append(other_host_id)

            hacker.swap_hosts_in_compromised_hosts(host_id, other_host_id)
        
        self.network.update_reachable_mtd()