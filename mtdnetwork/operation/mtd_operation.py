import random
from mtdnetwork.operation.time_generator import exponential_variates
import logging
import simpy
from mtdnetwork.network.mtd_scheme import MTDScheme


class MTDOperation:

    def __init__(self, env, network, adversary, attack_operation, scheme, proceed_time=0):
        self.env = env
        self.network = network
        self.adversary = adversary
        self._mtd_scheme = MTDScheme(network=network, scheme=scheme)
        self.attack_operation = attack_operation
        self._proceed_time = proceed_time
        self.application_layer_resource = simpy.Resource(self.env, 1)
        self.network_layer_resource = simpy.Resource(self.env, 1)
        self.reserve_resource = simpy.Resource(self.env, 1)

    def proceed_mtd(self):
        if self.network.get_unfinished_mtd() is not None:
            self.network.get_mtd_suspended_queue().appendleft(self.network.get_unfinished_mtd())
            self.network.set_unfinished_mtd(None)
        self.env.process(self.mtd_register_action())
        self.env.process(self.mtd_trigger_action())

    def mtd_register_action(self):
        """
        Register MTD(s) to the queue based on MTD scheme
        """
        while True:
            # terminate if the network is compromised
            if self.network.is_compromised(self.adversary.get_compromised_hosts()):
                return
            # register an MTD to the queue
            self._mtd_scheme.call_register_mtd()

            # exponential distribution for triggering MTD operations
            yield self.env.timeout(exponential_variates(self._mtd_scheme.get_mtd_register_interval(),
                                                        self._mtd_scheme.get_mtd_register_std()))

    def mtd_trigger_action(self):
        """
        trigger an MTD strategy in a given exponential time (next_mtd) in the queue
        Select Execute or suspend/discard MTD strategy
        based on the given resource occupation condition
        """
        while True:
            if not self.network.get_mtd_suspended_queue() and not self.network.get_mtd_strategy_queue():
                continue

            # trigger MTD
            mtd_strategy = self.trigger_mtd()
            logging.info('MTD: %s triggered %.1fs' % (mtd_strategy.get_name(), self.env.now + self._proceed_time))
            resource = self.mtd_resource(mtd_strategy)
            if resource is None or len(resource.users) == 0:
                self.env.process(self.mtd_execute_action(self.env, mtd_strategy))
            else:
                # suspend
                self.suspend_mtd(mtd_strategy)
                logging.info('MTD: %s suspended at %.1fs due to resource occupation' %
                             (mtd_strategy.get_name(), self.env.now + self._proceed_time))
                # discard TODO
            # exponential distribution for triggering MTD operations
            yield self.env.timeout(exponential_variates(self._mtd_scheme.get_mtd_trigger_interval(),
                                                        self._mtd_scheme.get_mtd_trigger_std()))

    def mtd_execute_action(self, env, mtd_strategy):
        """
        Action for executing MTD
        """
        # deploy mtd
        self.network.set_unfinished_mtd(mtd_strategy)
        request = self.mtd_resource(mtd_strategy).request()
        yield request
        start_time = env.now + self._proceed_time
        logging.info('MTD: %s deployed in the network at %.1fs.' % (mtd_strategy.get_name(), start_time))
        yield env.timeout(exponential_variates(mtd_strategy.get_execution_time_mean(),
                                               mtd_strategy.get_execution_time_std()))

        # if network is already compromised while executing mtd:
        if self.network.is_compromised(self.adversary.get_compromised_hosts()):
            return

        # execute mtd
        mtd_strategy.mtd_operation(self.adversary)

        finish_time = env.now + self._proceed_time
        duration = finish_time - start_time
        logging.info('MTD: %s finished in %.1fs at %.1fs.' % (mtd_strategy.get_name(), duration, finish_time))
        # release resource
        self.mtd_resource(mtd_strategy).release(request)
        # append execution records
        self.network.get_mtd_stats().append_mtd_operation_record(mtd_strategy, start_time, finish_time, duration)
        # interrupt adversary
        self.interrupt_adversary(env, mtd_strategy)

    def trigger_mtd(self):
        """
        pop up the MTD from the queue and trigger it.
        """
        self.network.get_mtd_stats().append_total_triggered()
        if len(self.network.get_mtd_suspended_queue()) != 0:
            return self.network.get_mtd_suspended_queue().popleft()
        return self.network.get_mtd_strategy_queue().popleft()

    def suspend_mtd(self, mtd_strategy):
        self.network.get_mtd_stats().append_total_suspended()
        self.network.get_mtd_suspended_queue().append(mtd_strategy)

    def mtd_resource(self, mtd_strategy):
        """Get the resource of the mtd"""
        if mtd_strategy.get_resource_type() == 'network':
            return self.network_layer_resource
        elif mtd_strategy.get_resource_type() == 'application':
            return self.application_layer_resource
        return self.reserve_resource

    def interrupt_adversary(self, env, mtd_strategy):
        # interrupt adversary attack process
        attack_process = self.attack_operation.get_attack_process()
        if attack_process is not None and attack_process.is_alive:
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
                    'MTD: Interrupted %s at %.1fs!' % (self.adversary.get_curr_process(),
                                                       env.now + self._proceed_time))
                self.network.get_mtd_stats().append_total_attack_interrupted()

    def get_proceed_time(self):
        return self._proceed_time

    def get_application_resource(self):
        return self.application_layer_resource

    def get_network_resource(self):
        return self.network_layer_resource

    def get_reserve_resource(self):
        return self.reserve_resource

    def get_mtd_scheme(self):
        return self._mtd_scheme

