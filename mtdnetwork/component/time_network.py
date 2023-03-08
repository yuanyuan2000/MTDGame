from mtdnetwork.component.network import Network
from mtdnetwork.statistic.mtd_statistics import MTDStatistics
from mtdnetwork.mtd.diversityassignment import DiversityAssignment
from mtdnetwork.component.host import Host
import random


class TimeNetwork(Network):

    def __init__(self, total_nodes=100, total_endpoints=10, total_subnets=10, total_layers=4,
                 target_layer=2, total_database=5):
        # default parameters
        self._mtd_stats = MTDStatistics()
        self._mtd_queue = []
        self._suspension_queue = dict()
        self._unfinished_mtd = dict()
        super().__init__(total_nodes=total_nodes, total_endpoints=total_endpoints, total_subnets=total_subnets,
                         total_layers=total_layers, target_layer=target_layer, total_database=total_database)
        self.init_network()
        self._diversity_assign = DiversityAssignment(graph=self.get_graph(),
                                                     sources=self.get_exposed_endpoints(),
                                                     dests=self.get_database(),
                                                     services=self.service_generator.get_all_generated_services(),
                                                     pos=self.pos,
                                                     colour_map=self.colour_map)

    def test(self):

        # return self._diversity_assign.calculate_variant_compromise_prob()
        return self._diversity_assign.objective()

    def setup_network(self):
        """
        Using the generated graph, generates a host for each node on the graph.
        """
        ip_addresses = []

        for host_id in self.nodes:
            node_os = Host.get_random_os()
            node_os_version = Host.get_random_os_version(node_os)
            node_ip = Host.get_random_address(existing_addresses=ip_addresses)
            ip_addresses.append(node_ip)
            self.graph.nodes[host_id]["host"] = Host(
                node_os,
                node_os_version,
                host_id,
                node_ip,
                random.choices(self.users_list, k=self.users_per_host),
                self,
                self.service_generator
            )

        # todo: diversity assignment

    def is_compromised(self, compromised_hosts):
        # TODO: refactor terminating condition
        super().is_compromised(compromised_hosts)
        pass

    def get_mtd_stats(self):
        return self._mtd_stats

    def get_mtd_queue(self):
        return self._mtd_queue

    def get_suspended_mtd(self):
        return self._suspension_queue

    def get_unfinished_mtd(self):
        return self._unfinished_mtd

    def set_unfinished_mtd(self, mtd):
        self._unfinished_mtd[mtd.get_resource_type()] = mtd

    def get_dap(self):
        return self._diversity_assign




