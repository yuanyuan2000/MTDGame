from mtdnetwork.mtd import *


class ServiceDiversity(MTD):
    def __init__(self, network, mtd_operation, shuffles=50):
        self.logger = logging.getLogger("mtd:serviceDiversity")
        self.shuffles = shuffles
        super().__init__(name="serviceDiversity", network=network,  resource_type='application',
                         resource=mtd_operation.get_application_resource(), execution_time_mean=40, execution_time_std=0.5)

    def mtd_operation(self, adversary=None):
        self.logger.debug("changing services on hosts")
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
        # Update Attack Path Exposure for target networks
        if self.network.get_network_type() == 0:
            self.network.add_attack_path_exposure()
