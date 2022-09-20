import simpy
from mtdnetwork.network.targetnetwork import Network as TargetNetwork
from mtdnetwork.network.time_network import TimeNetwork
from mtdnetwork.event.mtd_operation import mtd_trigger_action
from mtdnetwork.constants import ATTACKER_THRESHOLD
from mtdnetwork.event.adversary import Adversary
from mtdnetwork.mtd.osdiversity import OSDiversity
from mtdnetwork.mtd.servicediversity import ServiceDiversity
import logging

logging.basicConfig(format='%(message)s', level=logging.INFO)
# Simulation time in seconds
SIM_TIME = 30000

# parameters for mtd triggering
MTD_TRIGGER_MEAN = 60


def create_network(env):
    target_network = TargetNetwork(total_nodes=200, total_endpoints=20, total_subnets=20, total_layers=5,
                                   target_layer=2)
    graph = target_network.get_graph_copy()
    colour_map = target_network.get_colourmap()
    pos = target_network.get_pos()
    node_per_layer = target_network.get_node_per_layer()
    users_list = target_network.get_users_list()
    users_per_host = target_network.get_users_per_host()
    time_network = TimeNetwork(env, graph, pos, colour_map, 200, 20, 20, 5, node_per_layer, users_list, users_per_host)
    return time_network


def run_sim():
    # set up event execution environment
    env = simpy.Environment()

    # initialise network to perform MTD strategies
    time_network = create_network(env)
    time_network.initialise_mtd_schedule(mtd_interval_schedule=MTD_TRIGGER_MEAN,
                                         mtd_strategy_schedule=[OSDiversity, ServiceDiversity],
                                         timestamps=[10000, 20000],
                                         compromised_ratios=[0.2, 0.5])

    # triggering adversary
    adversary = Adversary(env=env, network=time_network, attack_threshold=ATTACKER_THRESHOLD)

    # triggering mtd events
    env.process(mtd_trigger_action(env=env, network=time_network,
                                   adversary=adversary))

    # Execute!
    env.run(until=SIM_TIME)

    return time_network.mtd_stats, adversary.attack_stats


if __name__ == "__main__":
    run_sim()
