import simpy
import logging
import os
import pandas as pd
from mtdnetwork.component.time_network import TimeNetwork
from mtdnetwork.operation.mtd_operation import MTDOperation
from mtdnetwork.data.constants import ATTACKER_THRESHOLD
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
    evaluations = []
    for mtd in mtd_strategies:
        for mtd_trigger_interval in [100, 200, 400, 700, 1200, 2000]:
            # initialise the simulation
            env = simpy.Environment()
            snapshot_checkpoint = SnapshotCheckpoint()
            try:
                time_network, adversary = snapshot_checkpoint.load_snapshots(0)
            except FileNotFoundError:
                time_network = TimeNetwork()
                adversary = Adversary(network=time_network, attack_threshold=ATTACKER_THRESHOLD)
                snapshot_checkpoint.save_initialised(time_network, adversary)

            # start attack
            attack_operation = AttackOperation(env=env, adversary=adversary, proceed_time=0)
            attack_operation.proceed_attack()

            # start mtd
            if mtd:
                mtd_operation = MTDOperation(env=env, network=time_network, scheme='single',
                                             attack_operation=attack_operation, proceed_time=0,
                                             mtd_trigger_interval=mtd_trigger_interval, custom_strategies=mtd)
                mtd_operation.proceed_mtd()

            # start simulation
            env.run(until=10000)
            evaluation = Evaluation(network=time_network, adversary=adversary)

            if not mtd:
                mtd_name = "NoMTD"
            else:
                mtd_name = mtd(network=time_network).get_name()

            evaluations.append({
                'Name': mtd_name,
                'MTD Interval': mtd_trigger_interval,
                'MTTC': evaluation.mean_time_to_compromise(),
                'MEF': evaluation.mtd_execution_frequency(),
                'ASR': evaluation.attack_success_rate(),
                'Compromised Num': evaluation.compromised_num()
            })
        print("Finished simulation for " + mtd_name + "!")
    # current_directory = os.getcwd()
    # if not os.path.exists(current_directory + '\\data_analysis'):
    #     os.makedirs(current_directory + '\\data_analysis')
    # pd.DataFrame(evaluations).to_csv('data_analysis/single_mtd_sim.csv', index=False)
    return evaluations


def multiple_mtd_simulation():
    evaluations = []
    for scheme in ['random', 'alternative', 'simultaneous']:
        for mtd_trigger_interval in [100, 200, 400, 700, 1200, 2000]:
            evaluation = main(start_time=0, finish_time=10000, scheme=scheme, mtd_trigger_interval=mtd_trigger_interval)
            evaluations.append({
                'Name': scheme,
                'MTD Interval': mtd_trigger_interval,
                'MTTC': evaluation.mean_time_to_compromise(),
                'MEF': evaluation.mtd_execution_frequency(),
                'ASR': evaluation.attack_success_rate(),
                'Compromised Num': evaluation.compromised_num()
            })
        print("Finished simulation for " + scheme + "!")
    # current_directory = os.getcwd()
    # if not os.path.exists(current_directory + '\\data_analysis'):
    #     os.makedirs(current_directory + '\\data_analysis')
    # pd.DataFrame(evaluations).to_csv('data_analysis/multiple_mtd_sim.csv', index=False)
    return evaluations


def main(start_time=-1, finish_time=1000, scheme='randomly', mtd_trigger_interval=None, checkpoints=None):
    # initialise the simulation
    env = simpy.Environment()
    snapshot_checkpoint = SnapshotCheckpoint(env=env, checkpoints=checkpoints)
    # load saved snapshots
    if start_time > -1:
        time_network, adversary = snapshot_checkpoint.load_snapshots(start_time)
    # initialise the network and the adversary
    else:
        start_time = 0
        time_network = TimeNetwork()
        adversary = Adversary(network=time_network, attack_threshold=ATTACKER_THRESHOLD)

    # start attack
    attack_operation = AttackOperation(env=env, adversary=adversary, proceed_time=start_time)
    attack_operation.proceed_attack()

    # start mtd
    if scheme != 'None':
        mtd_operation = MTDOperation(env=env, network=time_network, scheme=scheme,
                                     attack_operation=attack_operation, mtd_trigger_interval=mtd_trigger_interval,
                                     proceed_time=start_time)
        mtd_operation.proceed_mtd()

    # save snapshot
    if checkpoints is not None:
        snapshot_checkpoint.proceed_save(time_network, adversary)

    # start simulation
    env.run(until=(finish_time - start_time))

    # time_network.get_mtd_stats().save_record(sim_time=finish_time, scheme=scheme)
    # adversary.get_attack_stats().save_record(sim_time=finish_time, scheme=scheme)
    evaluation = Evaluation(network=time_network, adversary=adversary)
    return evaluation


if __name__ == "__main__":
    main()
