from mtdnetwork.mtd import *

class HostShuffle(MTD):

    def __init__(self, network):
        self.logger = logging.getLogger("mtd:hostshuffle")
        super().__init__(network)

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

        for host_id, host_instance in hosts.items():
            other_host_id = self.random_different_host_id(host_id, host_id_list)
            other_host_instance = hosts[other_host_id]

            host_instance.host_id = other_host_id
            other_host_instance.host_id = host_id

            self.network.graph.nodes[host_id]["host"] = other_host_instance
            self.network.graph.nodes[other_host_id]["host"] = host_instance

            hacker.swap_host_ids_in_compromised(host_id, other_host_id)