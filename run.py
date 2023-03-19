import simpy
import logging
import os
import pandas as pd
from mtdnetwork.component.time_network import TimeNetwork
from mtdnetwork.operation.mtd_operation import MTDOperation
from mtdnetwork.data.constants import ATTACKER_THRESHOLD, OS_TYPES
from mtdnetwork.component.adversary import Adversary
from mtdnetwork.operation.attack_operation import AttackOperation
from mtdnetwork.snapshot.snapshot_checkpoint import SnapshotCheckpoint
from mtdnetwork.statistic.evaluation import Evaluation
from mtdnetwork.mtd.completetopologyshuffle import CompleteTopologyShuffle
from mtdnetwork.mtd.ipshuffle import IPShuffle
from mtdnetwork.mtd.hosttopologyshuffle import HostTopologyShuffle
from mtdnetwork.mtd.portshuffle import PortShuffle
from mtdnetwork.mtd.osdiversity import OSDiversity
from mtdnetwork.mtd.servicediversity import ServiceDiversity
from mtdnetwork.mtd.usershuffle import UserShuffle
from mtdnetwork.mtd.osdiversityassignment import OSDiversityAssignment, DiversityAssignment
import random

# logging.basicConfig(format='%(message)s', level=logging.INFO)

mtd_strategies = [
    None,
    CompleteTopologyShuffle,
    # HostTopologyShuffle,
    IPShuffle,
    OSDiversity,
    PortShuffle,
    ServiceDiversity,
    # UserShuffle
]


def single_mtd_simulation():
    """
    Deploying single MTD in the mtd_strategies for each simulation
    """
    evaluations = []
    for mtd in mtd_strategies:
        if mtd is None:
            scheme = 'None'
            mtd_name = "NoMTD"
        else:
            mtd_name = mtd().get_name()
            scheme = 'single'
        for mtd_interval in [100, 150, 200]:
            for network_size in [30, 50, 70, 90]:
                evaluation = mtd_execution(scheme=scheme, mtd_interval=mtd_interval,
                                           custom_strategies=mtd, total_nodes=network_size)
                evaluate = evaluation.time_to_compromise_and_attack_success_rate_by_checkpoint()
                for item in evaluate:
                    evaluations.append({
                        'Name': mtd_name,
                        'mtd_interval': mtd_interval,
                        'MEF': evaluation.mtd_execution_frequency(),
                        'ASR': item['attack_success_rate'],
                        'time_to_compromise': item['time_to_compromise'],
                        'host_compromise_ratio': item['host_compromise_ratio'],
                        'network_size': network_size
                        # 'Compromised Num': evaluation.compromised_num()
                    })
        print("Finished simulation for " + mtd_name + "!")
    return evaluations


def dap_mtd_simulation():
    snapshot_checkpoint = SnapshotCheckpoint()
    os_types_list = [random.sample(OS_TYPES, 2), random.sample(OS_TYPES, 3), OS_TYPES]
    evaluations = []
    for os_types in os_types_list:
        for mtd_interval in [100]:
            for network_size in [20, 50, 80]:
                time_network, adversary = snapshot_checkpoint.load_snapshots_by_network_size(network_size)
                mtd = OSDiversityAssignment(network=time_network, os_types=os_types)
                evaluation = mtd_execution(scheme='single', mtd_interval=mtd_interval,
                                           custom_strategies=mtd, total_nodes=network_size)
                evaluate = evaluation.time_to_compromise_and_attack_success_rate_by_checkpoint()
                for item in evaluate:
                    evaluations.append({
                        'Name': mtd.get_name(),
                        'mtd_interval': mtd_interval,
                        'MEF': evaluation.mtd_execution_frequency(),
                        'ASR': item['attack_success_rate'],
                        'time_to_compromise': item['time_to_compromise'],
                        'host_compromise_ratio': item['host_compromise_ratio'],
                        'network_size': network_size
                        # 'Compromised Num': evaluation.compromised_num()
                    })
    return evaluations


def multiple_mtd_simulation():
    evaluations = []
    for scheme in ['random', 'alternative', 'simultaneous']:
        for mtd_interval in [100, 150, 200]:
            for network_size in [30, 50, 70, 90]:
                evaluation = mtd_execution(scheme=scheme, mtd_interval=mtd_interval, total_nodes=network_size)
                time_to_compromise = evaluation.time_to_compromise_and_attack_success_rate_by_checkpoint()
                for item in time_to_compromise:
                    evaluations.append({
                        'Name': scheme,
                        'mtd_interval': mtd_interval,
                        'MEF': evaluation.mtd_execution_frequency(),
                        'ASR': evaluation.attack_success_rate(),
                        'time_to_compromise': item['time_to_compromise'],
                        'host_compromise_ratio': item['host_compromise_ratio'],
                        'network_size': network_size
                        # 'Compromised Num': evaluation.compromised_num()
                    })
        print("Finished simulation for " + scheme + "!")
    return evaluations


def mtd_execution(start_time=0, finish_time=None, scheme='random', mtd_interval=None, custom_strategies=None,
                  checkpoints=None, total_nodes=50, total_endpoints=3, total_subnets=8, total_layers=4,
                  target_layer=4, total_database=2, new_network=False):
    # initialise the simulation
    env = simpy.Environment()
    end_event = env.event()
    snapshot_checkpoint = SnapshotCheckpoint(env=env, checkpoints=checkpoints)
    if not new_network:
        time_network, adversary = snapshot_checkpoint.load_snapshots_by_network_size(total_nodes)
    # try:
    #
    # except FileNotFoundError:
    else:
        time_network = TimeNetwork(total_nodes=total_nodes, total_endpoints=total_endpoints,
                                   total_subnets=total_subnets, total_layers=total_layers,
                                   target_layer=target_layer, total_database=total_database)
        adversary = Adversary(network=time_network, attack_threshold=ATTACKER_THRESHOLD)
        # snapshot_checkpoint.save_initialised(time_network, adversary)
        snapshot_checkpoint.save_snapshots_by_network_size(time_network, adversary)

    # start attack
    attack_operation = AttackOperation(env=env, end_event=end_event, adversary=adversary, proceed_time=0)
    attack_operation.proceed_attack()

    # start mtd
    if scheme != 'None':
        mtd_operation = MTDOperation(env=env, end_event=end_event, network=time_network, scheme=scheme,
                                     attack_operation=attack_operation, proceed_time=0,
                                     mtd_trigger_interval=mtd_interval, custom_strategies=custom_strategies)
        mtd_operation.proceed_mtd()

        # save snapshot
    if checkpoints is not None:
        snapshot_checkpoint.proceed_save(time_network, adversary)

    # start simulation
    if finish_time is not None:
        env.run(until=(finish_time - start_time))
    else:
        env.run(until=end_event)
    evaluation = Evaluation(network=time_network, adversary=adversary)

    # sim_item = scheme
    # if scheme == 'single':
    #     sim_item = custom_strategies().get_name()
    # elif scheme == 'None':
    #     sim_item = 'NoMTD'
    # time_network.get_mtd_stats().save_record(sim_time=mtd_interval, scheme=sim_item)
    # adversary.get_attack_stats().save_record(sim_time=mtd_interval, scheme=sim_item)

    return evaluation


if __name__ == "__main__":
    mtd_execution()
