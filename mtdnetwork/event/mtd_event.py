import random
from scipy.stats import norm
from scipy.stats import expon
from mtdnetwork.mtd.completetopologyshuffle import CompleteTopologyShuffle
from mtdnetwork.mtd.ipshuffle import IPShuffle
from mtdnetwork.mtd.hosttopologyshuffle import HostTopologyShuffle
from mtdnetwork.mtd.portshuffle import PortShuffle
from mtdnetwork.mtd.osdiversity import OSDiversity
from mtdnetwork.mtd.servicediversity import ServiceDiversity

# parameters for mtd triggering
MTD_TRIGGER_MEAN = 30

# parameters for capacity of application layer and network layer
AL_CAPACITY = 1
NL_CAPACITY = 1
MTD_STRATEGIES = [CompleteTopologyShuffle, IPShuffle, HostTopologyShuffle,
                  PortShuffle, OSDiversity, ServiceDiversity]


def mtd_trigger_action(env, network, al_resource, nl_resource, adversary, mtd_operation_record):
    """
    trigger an MTD strategy in a given exponential time (next_mtd)
    """
    while True:
        # exponential distribution for triggering MTD operations
        next_mtd = expon.rvs(scale=MTD_TRIGGER_MEAN, size=1)[0]
        yield env.timeout(next_mtd)
        # register an MTD to the queue
        network.register_mtd(random.choice(MTD_STRATEGIES))

        # trigger MTD
        mtd_strategy = network.trigger_mtd()
        print('MTD: %s triggered %.1fs' % (mtd_strategy.name, env.now))
        # nl resource
        if mtd_strategy.resource_type == 'network':
            execute_or_suspend(env, mtd_strategy, network, nl_resource, adversary, mtd_operation_record)
        elif mtd_strategy.resource_type == 'application':
            execute_or_suspend(env, mtd_strategy, network, al_resource, adversary, mtd_operation_record)


def execute_or_suspend(env, mtd_strategy, network, resource, adversary, mtd_operation_record):
    """
    Select Execute or suspend/discard MTD strategy
    based on the given resource occupation condition
    """

    if len(resource.users) == 0:
        env.process(mtd_execute_action(env, mtd_strategy, resource, adversary, mtd_operation_record))
    else:
        # suspend
        network.suspended_queue.append(mtd_strategy)
        print('MTD: %s suspended at %.1fs due to resource occupation' % (mtd_strategy.name, env.now))
        # discard
        pass


def mtd_execute_action(env, mtd_strategy, resource, adversary, mtd_operation_record):
    """
    Action for executing MTD
    """
    # deploy mtd
    occupied_resource = resource.request()
    yield occupied_resource
    start_time = env.now
    print('MTD: %s deployed in the network at %.1fs.' % (mtd_strategy.name, start_time))

    # execute mtd
    mtd_strategy.mtd_operation()
    execution_time = expon.rvs(scale=mtd_strategy.execution_time, size=1)[0]

    yield env.timeout(execution_time)

    finish_time = env.now
    duration = env.now - start_time
    print('MTD: %s finished in %.1fs at %.1fs.' % (mtd_strategy.name, duration, finish_time))
    mtd_operation_record.append({
        'name': mtd_strategy.name,
        'start_time': start_time,
        'finish_time': finish_time,
        'duration': duration
    })
    # release resource
    resource.release(occupied_resource)

    # interrupt adversary attack process
    if adversary.attack_process is not None and adversary.attack_process.is_alive:
        adversary.interrupted_in = 'Network Layer' if mtd_strategy.resource_type == 'network' else 'Application Layer'
        adversary.interrupted_by = mtd_strategy.name
        adversary.attack_process.interrupt()
        print('MTD: Interrupted %s at %.1fs!' % (adversary.curr_process, env.now))


        # elif adversary.
