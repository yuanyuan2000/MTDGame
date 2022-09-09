import random
from scipy.stats import norm
from scipy.stats import expon
from mtdnetwork.mtd.ipshuffle import IPShuffle
from mtdnetwork.mtd.hosttopologyshuffle import HostTopologyShuffle
from mtdnetwork.mtd.portshuffle import PortShuffle

# parameters for mtd triggering
MTD_TRIGGER_MEAN = 30

# parameters for capacity of application layer and network layer
AL_CAPACITY = 1
NL_CAPACITY = 1
MTD_STRATEGIES = [IPShuffle, HostTopologyShuffle, PortShuffle]


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
        print('%s triggered %.1fs' % (mtd_strategy.name, env.now))
        # nl resource
        if mtd_strategy.resource == 'network':
            execute_or_suspend(env, mtd_strategy, network, nl_resource, adversary, mtd_operation_record)
        elif mtd_strategy.resource == 'application':
            execute_or_suspend(env, mtd_strategy, network, al_resource, mtd_operation_record)


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
        print('%s suspended at %.1fs due to resource occupation' % (mtd_strategy.name, env.now))
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
    print('%s deployed in the network at %.1fs.' % (mtd_strategy.name, start_time))

    # execute mtd
    mtd_strategy.mtd_operation()
    execution_time = expon.rvs(scale=mtd_strategy.execution_time, size=1)[0]

    yield env.timeout(execution_time)
    # interrupt adversary attack process
    if mtd_strategy.resource == 'network':
        if adversary.port_scan_process is not None:
            # interrupt port scan
            adversary.port_scan_process.interrupt()
            print('Port scan has been interrupted!')
        elif adversary.exploit_vulnerabilities_process is not None:
            # interrupt exploit vulnerabilities
            adversary.exploit_vulnerabilities_process.interrupt()
            print('Exploit vulnerabilities has been interrupted!')
        elif adversary.brute_force_process is not None:
            # interrupt brute force
            adversary.brute_force_process.interrupt()
            print('Brute force has been interrupted!')
        # elif adversary.

    finish_time = env.now
    duration = env.now - start_time
    print('%s finished in %.1fs at %.1fs.' % (mtd_strategy.name, duration, finish_time))
    mtd_operation_record.append({
        'name': mtd_strategy.name,
        'start_time': start_time,
        'finish_time': finish_time,
        'duration': duration
    })
    # release resource
    resource.release(occupied_resource)
