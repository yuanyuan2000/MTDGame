from mtdnetwork.mtd import *

class ServiceShuffle(MTD):
    def __init__(self, network, shuffles=50):
        self.logger = logging.getLogger("mtd:serviceshuffle")
        self.shuffles = shuffles
        super().__init__("ServiceShuffle", network)

    def mtd_operation(self):
        self.logger.info("changing services on hosts")
        service_generator = self.network.get_service_generator()
        hosts = self.network.get_hosts()
        for host_id, host_instance in hosts.items():
            if host_id in self.network.exposed_endpoints:
                continue
            host_instance = random.choice(hosts)
            for node_id in range(host_instance.total_nodes):
                if node_id == host_instance.target_node:
                    continue
                host_instance.graph.nodes[node_id]["service"] = service_generator.get_random_service_latest_version(
                    host_instance.os_type, 
                    host_instance.os_version
                )