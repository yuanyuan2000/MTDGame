import simpy
import logging
from mtdnetwork.component.time_network import TimeNetwork
from mtdnetwork.operation.mtd_operation import MTDOperation
from mtdnetwork.data.constants import ATTACKER_THRESHOLD
from mtdnetwork.component.adversary import Adversary
from mtdnetwork.operation.attack_operation import AttackOperation
from mtdnetwork.snapshot.snapshot_checkpoint import SnapshotCheckpoint
from mtdnetwork.statistic.metrics import Metrics

logging.basicConfig(format='%(message)s', level=logging.INFO)


def main(start_time=0, finish_time=1000, scheme='randomly', checkpoints=None):
    # initialise the simulation
    env = simpy.Environment()
    snapshot_checkpoint = SnapshotCheckpoint(env=env, checkpoints=checkpoints)
    # load saved snapshots
    if start_time != 0:
        time_network, adversary = snapshot_checkpoint.load_snapshots(start_time)
    # initialise the network and the adversary
    else:
        time_network = TimeNetwork()
        adversary = Adversary(network=time_network, attack_threshold=ATTACKER_THRESHOLD)

    # start attack
    attack_operation = AttackOperation(env=env, adversary=adversary, proceed_time=start_time)
    attack_operation.proceed_attack()

    # start mtd
    if scheme != 'None':
        mtd_operation = MTDOperation(env=env, network=time_network, scheme=scheme,
                                     attack_operation=attack_operation, proceed_time=start_time)
        mtd_operation.proceed_mtd()

    # save snapshot
    if checkpoints is not None:
        snapshot_checkpoint.proceed_save(time_network, adversary)

    # start simulation
    env.run(until=(finish_time - start_time))

    time_network.get_mtd_stats().save_record(sim_time=finish_time, scheme=scheme)
    adversary.get_attack_stats().save_record(sim_time=finish_time, scheme=scheme)
    metrics = Metrics(network=time_network, adversary=adversary)
    return metrics


if __name__ == "__main__":
    main()
