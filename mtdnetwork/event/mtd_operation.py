import random
from mtdnetwork.event.time_generator import exponential_variates
import logging
import simpy
from collections import deque

MTD_TRIGGER_STD = 0.5


class MTDOperation:

    def __init__(self, env, network, adversary, attack_operation):
        self.env = env
        self.network = network
        self.adversary = adversary
        self.attack_operation = attack_operation
        self._proceed_time = 0
        self._mtd_strategy_queue = deque()
        self._suspended_queue = deque()
        self.application_layer_resource = simpy.Resource(self.env, 1)
        self.network_layer_resource = simpy.Resource(self.env, 1)
        self.reserve_resource = simpy.Resource(self.env, 1)

    def proceed_mtd(self):
        self.env.process(self.mtd_trigger_action())

    def mtd_trigger_action(self):
        """
        trigger an MTD strategy in a given exponential time (next_mtd)

        Select Execute or suspend/discard MTD strategy
        based on the given resource occupation condition
        """
        mtd_interval = self.network.get_mtd_schedule().get_mtd_interval_schedule()
        mtd_strategies = self.network.get_mtd_schedule().get_mtd_strategy_schedule()
        while not self.network.is_compromised(self.adversary.get_compromised_hosts()):
            # mtd_interval = network.get_mtd_schedule().adapt_schedule_by_time(env)
            # mtd_strategies = network.get_mtd_schedule().adapt_schedule_by_compromised_ratio(
            #     env, network.compromised_ratio(len(adversary.get_compromised_hosts())))

            # exponential distribution for triggering MTD operations
            yield self.env.timeout(exponential_variates(mtd_interval, MTD_TRIGGER_STD))

            # register an MTD to the queue
            self.register_mtd(random.choice(mtd_strategies))

            # trigger MTD
            mtd_strategy = self.trigger_mtd()
            logging.info('MTD: %s triggered %.1fs' % (mtd_strategy.name, self.env.now + self._proceed_time))
            if mtd_strategy.resource is None or len(mtd_strategy.resource.users) == 0:
                self.env.process(self.mtd_execute_action(self.env, mtd_strategy))
            else:
                # suspend
                self.suspend_mtd(mtd_strategy)
                logging.info('MTD: %s suspended at %.1fs due to resource occupation' %
                             (mtd_strategy.name, self.env.now + self._proceed_time))
                # discard todo

    def mtd_execute_action(self, env, mtd_strategy):
        """
        Action for executing MTD
        """
        # deploy mtd
        occupied_resource = mtd_strategy.resource.request()
        yield occupied_resource
        start_time = env.now + self._proceed_time
        logging.info('MTD: %s deployed in the network at %.1fs.' % (mtd_strategy.name, start_time))
        yield env.timeout(exponential_variates(mtd_strategy.get_execution_time_mean(),
                                               mtd_strategy.get_execution_time_std()))

        # if network is already compromised while executing mtd:
        if self.network.is_compromised(self.adversary.get_compromised_hosts()):
            return

        # execute mtd
        mtd_strategy.mtd_operation(self.adversary)

        finish_time = env.now + self._proceed_time
        duration = finish_time - start_time
        logging.info('MTD: %s finished in %.1fs at %.1fs.' % (mtd_strategy.name, duration, finish_time))
        # release resource
        mtd_strategy.resource.release(occupied_resource)

        # append execution records
        self.network.get_mtd_stats().append_mtd_operation_record(mtd_strategy, start_time, finish_time, duration)
        # interrupt adversary attack process
        if self.attack_operation.get_attack_process() is not None and self.attack_operation.get_attack_process().is_alive:
            if mtd_strategy.get_resource_type() == 'network':
                self.attack_operation.set_interrupted_mtd(mtd_strategy)
                self.attack_operation.get_attack_process().interrupt()
                logging.info(
                    'MTD: Interrupted %s at %.1fs!' % (self.adversary.get_curr_process(),
                                                       env.now + self._proceed_time))
                self.network.get_mtd_stats().append_total_attack_interrupted()
            elif mtd_strategy.get_resource_type() == 'application' and \
                    self.adversary.get_curr_process() not in [
                                                            'SCAN_HOST',
                                                            'ENUM_HOST',
                                                            'SCAN_NEIGHBOR']:
                self.attack_operation.set_interrupted_mtd(mtd_strategy)
                self.attack_operation.get_attack_process().interrupt()
                logging.info(
                    'MTD: Interrupted %s at %.1fs!' % (self.adversary.get_curr_process(), env.now + self._proceed_time))
                self.network.get_mtd_stats().append_total_attack_interrupted()

    def register_mtd(self, mtd_strategy):
        """
        Registers an MTD strategy that will reconfigure the Network during the simulation to try and thwart the hacker.

        Paramters:
            mtd_strategy:
                an instance of MTDStrategy that the network will use to reconfigure the network
        """
        mtd_strategy = mtd_strategy(self.network, self)
        self._mtd_strategy_queue.append(mtd_strategy)

    def trigger_mtd(self):
        """
        pop up the MTD and trigger it.
        :return:
        """
        self.network.get_mtd_stats().total_triggered += 1
        if len(self._suspended_queue) != 0:
            return self._suspended_queue.popleft()
        return self._mtd_strategy_queue.popleft()

    def suspend_mtd(self, mtd_strategy):
        self.network.get_mtd_stats().total_suspended += 1
        self._suspended_queue.append(mtd_strategy)

    def get_proceed_time(self):
        return self._proceed_time

    def set_proceed_time(self, proceed_time):
        self._proceed_time = proceed_time

    def get_application_resource(self):
        return self.application_layer_resource

    def get_network_resource(self):
        return self.network_layer_resource

    def get_reserve_resource(self):
        return self.reserve_resource
