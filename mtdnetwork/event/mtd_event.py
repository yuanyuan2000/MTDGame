import random
from mtdnetwork.event.time_generator import exponential_variates
from mtdnetwork.mtd.completetopologyshuffle import CompleteTopologyShuffle
from mtdnetwork.mtd.ipshuffle import IPShuffle
from mtdnetwork.mtd.hosttopologyshuffle import HostTopologyShuffle
from mtdnetwork.mtd.portshuffle import PortShuffle
from mtdnetwork.mtd.osdiversity import OSDiversity
from mtdnetwork.mtd.servicediversity import ServiceDiversity
from mtdnetwork.mtd.usershuffle import UserShuffle
import logging

# parameters for mtd triggering
MTD_TRIGGER_MEAN = 30
MTD_TRIGGER_STD = 0.5

# parameters for capacity of application layer and network layer
MTD_STRATEGIES = [CompleteTopologyShuffle, IPShuffle, HostTopologyShuffle,
                  PortShuffle, OSDiversity, ServiceDiversity, UserShuffle]


def mtd_trigger_action(env, network, adversary):
    """
    trigger an MTD strategy in a given exponential time (next_mtd)

    Select Execute or suspend/discard MTD strategy
    based on the given resource occupation condition
    """
    while not network.is_compromised(adversary.compromised_hosts):
        # exponential distribution for triggering MTD operations
        yield env.timeout(exponential_variates(MTD_TRIGGER_MEAN, MTD_TRIGGER_STD))

        # register an MTD to the queue
        network.register_mtd(random.choice(MTD_STRATEGIES))

        # trigger MTD
        mtd_strategy = network.trigger_mtd()
        logging.info('MTD: %s triggered %.1fs' % (mtd_strategy.name, env.now))
        if mtd_strategy.resource is None or len(mtd_strategy.resource.users) == 0:
            env.process(mtd_execute_action(env, mtd_strategy, network, adversary))
        else:
            # suspend
            network.suspend_mtd(mtd_strategy)
            logging.info('MTD: %s suspended at %.1fs due to resource occupation' %
                                      (mtd_strategy.name, env.now))
            # discard todo


def mtd_execute_action(env, mtd_strategy, network, adversary):
    """
    Action for executing MTD
    """
    # deploy mtd
    occupied_resource = mtd_strategy.resource.request()
    yield occupied_resource
    start_time = env.now
    logging.info('MTD: %s deployed in the network at %.1fs.' % (mtd_strategy.name, start_time))
    yield env.timeout(exponential_variates(mtd_strategy.execution_time_mean, mtd_strategy.execution_time_std))
    # execute mtd
    mtd_strategy.mtd_operation(adversary)

    finish_time = env.now
    duration = env.now - start_time
    logging.info('MTD: %s finished in %.1fs at %.1fs.' % (mtd_strategy.name, duration, finish_time))
    # release resource
    mtd_strategy.resource.release(occupied_resource)

    # append execution records
    network.mtd_stats.append_mtd_operation_record(mtd_strategy, start_time, finish_time, duration)
    # interrupt adversary attack process
    if adversary.attack_process is not None and adversary.attack_process.is_alive:
        if mtd_strategy.resource_type == 'network':
            adversary.interrupted_mtd = mtd_strategy
            adversary.attack_process.interrupt()
            logging.info('MTD: Interrupted %s at %.1fs!' % (adversary.curr_process, env.now))
            network.mtd_stats.total_attack_interrupted += 1
        elif mtd_strategy.resource_type == 'application' and adversary.curr_process not in ['SCAN_HOST', 'ENUM_HOST']:
            adversary.interrupted_mtd = mtd_strategy
            adversary.attack_process.interrupt()
            logging.info('MTD: Interrupted %s at %.1fs!' % (adversary.curr_process, env.now))
            network.mtd_stats.total_attack_interrupted += 1
