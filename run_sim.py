import time

import simpy
from mtdnetwork.network.time_network import TimeNetwork
from mtdnetwork.event.mtd_operation import mtd_trigger_action
from mtdnetwork.constants import ATTACKER_THRESHOLD
from mtdnetwork.event.adversary import Adversary
from mtdnetwork.state.network_state import NetworkState
from mtdnetwork.state.adversary_state import AdversaryState

import logging

logging.basicConfig(format='%(message)s', level=logging.INFO)
# Simulation time in seconds
SIM_TIME = 3000


def run_sim(time_network=None, adversary=None, now=0):
    # set up event execution environment
    env = simpy.Environment()
    if now == 0:
        time_network = TimeNetwork.create_network(env)
        adversary = Adversary(env=env, network=time_network, attack_threshold=ATTACKER_THRESHOLD)
    else:
        time_network.reconfigure_properties(env, now)
        adversary.reconfigure_properties(env, now)

    # start attack!
    adversary.proceed_attack()
    # triggering mtd operations
    env.process(mtd_trigger_action(env=env, network=time_network,
                                   adversary=adversary))

    # Execute!
    env.run(until=SIM_TIME)

    return env.now, time_network, adversary


def main():
    time_network = None
    adversary = None
    now = 0
    adversary_state = AdversaryState()
    network_state = NetworkState()
    for i in range(10):
        # time_network = network_state.load_network_state(now)
        # adversary = adversary_state.load_adversary(now)
        stop_time, time_network, adversary = run_sim(time_network, adversary, now)
        now += stop_time
        network_state.save_network_state(time_network, now)
        adversary_state.save_adversary(adversary, now)
        if time_network.is_compromised(adversary.compromised_hosts):
            return time_network, adversary
    return time_network, adversary


if __name__ == "__main__":
    main()
