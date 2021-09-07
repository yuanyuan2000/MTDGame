from mtdnetwork.mtd import *

class PortShuffle(MTD):

    def __init__(self, network):
        self.logger = logging.getLogger("mtd:portshuffle")
        super().__init__("PortShuffle", network)

    def mtd_operation(self):
        self.logger.info("changing ports of services on hosts")
        hosts = self.network.get_hosts()

        for host_id, host_instance in hosts.items():
            # Do not change exposed endpoints as other organisations might
            # require to be fixed
            if host_instance.host_id in self.network.exposed_endpoints:
                self.logger.debug("changing ports: skipping {} since it is an exposed endpoint".format(host_id))
                continue
            new_ports = []
            for node_id in host_instance.graph.nodes:
                if node_id == host_instance.target_node:
                    continue
                new_port = host.Host.get_random_port(
                    existing_ports=new_ports
                )
                new_ports.append(new_port)
                host_instance.graph.nodes[node_id]["port"] = new_port