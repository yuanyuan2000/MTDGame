from mtdnetwork.mtd import *

class CompleteTopologyShuffle(MTD):
    """
    Completely regenerates the network, preserving the hosts from previously.
    """

    def __init__(self, network):
        self.logger = logging.getLogger("mtd:basictopologyshuffle")
        super().__init__("CompleteTopologyShuffle", network)

    def mtd_operation(self):
        self.logger.info("shuffling entire network topology")
        hosts = self.network.get_hosts()
        colour_map = self.network.colour_map

        # Regenerate the network graph
        self.network.gen_graph()
        self.network.colour_map = colour_map
        for host_id, host_instance in hosts.items():
            self.network.graph.nodes[host_id]["host"] = host_instance
        self.network.update_reachable_mtd()

