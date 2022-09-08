from mtdnetwork.mtd import *


class IPShuffle(MTD):

    def __init__(self, network):
        self.logger = logging.getLogger("mtd:ipshuffle")
        super().__init__(name="IPShuffle", network=network, resource='network', execution_time=40)

    def mtd_operation(self):
        self.logger.info("changing IP addresses of hosts")

        hosts = self.network.get_hosts()

        ip_addresses = []
        for host_id, host_instance in hosts.items():
            if host_id in self.network.exposed_endpoints:
                continue
            host_ip = host.Host.get_random_address(existing_addresses=ip_addresses)
            ip_addresses.append(host_ip)
            host_instance.ip = host_ip
