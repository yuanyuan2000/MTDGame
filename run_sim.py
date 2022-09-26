import simpy
from mtdnetwork.network.time_network import TimeNetwork
from mtdnetwork.operation.mtd_operation import MTDOperation
from mtdnetwork.constants import ATTACKER_THRESHOLD
from mtdnetwork.network.adversary import Adversary
from mtdnetwork.operation.attack_operation import AttackOperation
from mtdnetwork.state.state_checkpoint import StateCheckpoint

import logging

logging.basicConfig(format='%(message)s', level=logging.INFO)
# Simulation time in seconds
SIM_TIME = 30000


# def run_state_save_sim(time_network=None, adversary=None, now=0):
#     # set up event execution environment
#     env = simpy.Environment()
#     if now == 0:
#         time_network = TimeNetwork.create_network(env)
#         adversary = Adversary(network=time_network, attack_threshold=ATTACKER_THRESHOLD)
#     else:
#         time_network.reconfigure_properties(env, now)
#         adversary.reconfigure_properties(env, now)
#
#     # start attack!
#     adversary.proceed_attack()
#     # triggering mtd operations
#     env.process(mtd_trigger_action(env=env, network=time_network,
#                                    adversary=adversary))
#
#     # Execute!
#     env.run(until=SIM_TIME)
#
#     return env.now, time_network, adversary


# def run_state_save_main():
#     time_network = None
#     adversary = None
#     now = 0
#     adversary_state = AdversaryState()
#     network_state = NetworkState()
#     for i in range(10):
#         time_network = network_state.load_network(now)
#         adversary = adversary_state.load_adversary(now)
#         stop_time, time_network, adversary = run_state_save_sim(time_network, adversary, now)
#         now += stop_time
#         network_state.save_network(time_network, now)
#         adversary_state.save_adversary(adversary, now)
#         if time_network.is_compromised(adversary.compromised_hosts):
#             return time_network, adversary
#     return time_network, adversary

def sim_from_state(check_time):
    env = simpy.Environment()
    time, time_network, adversary = StateCheckpoint.load_states(check_time)
    attack_operation = AttackOperation(env=env, adversary=adversary)
    mtd_operation = MTDOperation(env=env, network=time_network, adversary=adversary, attack_operation=attack_operation)
    attack_operation.set_proceed_time(time)
    mtd_operation.set_proceed_time(time)
    # start attack!
    attack_operation.proceed_attack()
    # triggering mtd operations
    mtd_operation.proceed_mtd()
    # Execute!
    env.run(until=SIM_TIME - time)
    return time_network, adversary


def main():
    # set up event execution environment
    env = simpy.Environment()
    time_network = TimeNetwork.create_network()
    adversary = Adversary(network=time_network, attack_threshold=ATTACKER_THRESHOLD)
    attack_operation = AttackOperation(env=env, adversary=adversary)
    mtd_operation = MTDOperation(env=env, network=time_network, adversary=adversary, attack_operation=attack_operation)
    state_checkpoint = StateCheckpoint(env=env, checkpoints=[5000, 7000, 10000, 12000, 15000])
    # save state
    state_checkpoint.proceed_save(time_network, adversary)
    # start attack!
    attack_operation.proceed_attack()
    # triggering mtd operations
    mtd_operation.proceed_mtd()
    # Execute!
    env.run(until=SIM_TIME)

    return time_network, adversary


if __name__ == "__main__":
    main()
