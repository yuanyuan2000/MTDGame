from mtdnetwork.mtd import MTD
from mtdnetwork.network import host


class IPShuffle(MTD):

    def __init__(self, network, priority=3):
        super().__init__(name="IPShuffle",
                         mtd_type='shuffle',
                         resource_type='network',
                         execution_time_mean=40,
                         execution_time_std=0.5,
                         priority=priority,
                         network=network)

    def mtd_operation(self, adversary=None):
        hosts = self.network.get_hosts()

        ip_addresses = []
        for host_id, host_instance in hosts.items():
            if host_id in self.network.exposed_endpoints:
                continue
            host_ip = host.Host.get_random_address(existing_addresses=ip_addresses)
            ip_addresses.append(host_ip)
            host_instance.ip = host_ip
