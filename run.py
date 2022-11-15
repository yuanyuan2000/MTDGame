import simpy
import logging
from mtdnetwork.network.time_network import TimeNetwork
from mtdnetwork.operation.mtd_operation import MTDOperation
from mtdnetwork.data.constants import ATTACKER_THRESHOLD
from mtdnetwork.network.adversary import Adversary
from mtdnetwork.operation.attack_operation import AttackOperation
from mtdnetwork.snapshot.snapshot_checkpoint import SnapshotCheckpoint


logging.basicConfig(format='%(message)s', level=logging.INFO)
# Simulation time in seconds
SIM_TIME = 30000


def main(start_time=0, finish_time=SIM_TIME, scheme='randomly', checkpoints=None):

    # initialise the simulation
    env = simpy.Environment()
    snapshot_checkpoint = SnapshotCheckpoint(env=env, checkpoints=checkpoints)
    # load saved snapshots
    if start_time != 0:
        time_network, adversary = snapshot_checkpoint.load_snapshots(start_time)
    # initialise the network and the adversary
    else:
        time_network = TimeNetwork.create_network()
        adversary = Adversary(network=time_network, attack_threshold=ATTACKER_THRESHOLD)

    # initialise operations
    attack_operation = AttackOperation(env=env, adversary=adversary, proceed_time=start_time)
    mtd_operation = MTDOperation(env=env, network=time_network, adversary=adversary, scheme=scheme,
                                 attack_operation=attack_operation, proceed_time=start_time)

    # start attack
    attack_operation.proceed_attack()

    # start mtd
    mtd_operation.proceed_mtd()

    # save snapshot
    if checkpoints is not None:
        snapshot_checkpoint.proceed_save(time_network, adversary)

    # start simulation
    env.run(until=(finish_time-start_time))
    return time_network, adversary


if __name__ == "__main__":
    main()
