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

        # Regenerate the network graph
        self.network.regen_graph()
        for host_id, host_instance in hosts.items():
            self.network.graph.nodes[host_id]["host"] = host_instance
        self.network.update_reachable_mtd()


        # Set nHosts per layer
        # Generate new graph with those number of hosts per layer
        # Replace the new nodes with the old host instances
