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
            self._mtd_scheme.suspend_mtd(self.network.get_unfinished_mtd())
            self.network.set_unfinished_mtd(None)
        if self._mtd_scheme.get_scheme() == 'simultaneously':
            self.env.process(self._mtd_batch_trigger_action())
        else:
            self.env.process(self._mtd_trigger_action())

    def _mtd_trigger_action(self):
        """
        trigger an MTD strategy in a given exponential time (next_mtd) in the queue
        Select Execute or suspend/discard MTD strategy
        based on the given resource occupation condition
        """
        while True:
            # terminate the simulation if the network is compromised
            if self.network.is_compromised(compromised_hosts=self.adversary.get_compromised_hosts()):
                return

            # register an MTD
            if not self.network.get_mtd_queue().queue:
                self._mtd_scheme.register_mtd()
            # trigger an MTD
            if self.network.get_suspended_mtd():
                mtd = self._mtd_scheme.trigger_suspended_mtd()
            else:
                mtd = self._mtd_scheme.trigger_mtd()
            logging.info('MTD: %s triggered %.1fs' % (mtd.get_name(), self.env.now + self._proceed_time))
            resource = self._get_mtd_resource(mtd)
            if len(resource.users) == 0:
                self.env.process(self._mtd_execute_action(env=self.env, mtd=mtd))
            else:
                # suspend
                self._mtd_scheme.suspend_mtd(mtd)
                logging.info('MTD: %s suspended at %.1fs due to resource occupation' %
                             (mtd.get_name(), self.env.now + self._proceed_time))
                # discard TODO
            # exponential time interval for triggering MTD operations
            yield self.env.timeout(exponential_variates(self._mtd_scheme.get_mtd_trigger_interval(),
                                                        self._mtd_scheme.get_mtd_trigger_std()))

    def _mtd_batch_trigger_action(self):
        """
        trigger all MTDs at a time with a fixed priority
        """
        while True:
            # terminate the simulation if the network is compromised
            if self.network.is_compromised(compromised_hosts=self.adversary.get_compromised_hosts()):
                return

            suspended_mtd = self.network.get_suspended_mtd()
            if suspended_mtd:
                # triggering the suspended MTDs by priority
                suspended_mtd_priorities = sorted(suspended_mtd.keys())
                for priority in suspended_mtd_priorities:
                    resource = self._get_mtd_resource(mtd=suspended_mtd[priority])
                    if len(resource.users) == 0:
                        mtd = self._mtd_scheme.trigger_suspended_mtd()
                        yield self.env.process(self._mtd_execute_action(env=self.env, mtd=mtd))
            else:
                # register and trigger all MTDs
                if not self.network.get_suspended_mtd() and not self.network.get_mtd_queue().queue:
                    self._mtd_scheme.register_mtd()
                while self.network.get_mtd_queue().queue:
                    mtd = self._mtd_scheme.trigger_mtd()
                    resource = self._get_mtd_resource(mtd=mtd)
                    if len(resource.users) == 0:
                        self.env.process(self._mtd_execute_action(env=self.env, mtd=mtd))
                    else:
                        # suspend MTD if resource is occupied
                        self._mtd_scheme.suspend_mtd(mtd_strategy=mtd)

            # exponential distribution for triggering MTD operations
            yield self.env.timeout(exponential_variates(self._mtd_scheme.get_mtd_trigger_interval(),
                                                        self._mtd_scheme.get_mtd_trigger_std()))

    def _mtd_execute_action(self, env, mtd):
        """
        Action for executing MTD
        """
        # deploy mtd
        self.network.set_unfinished_mtd(mtd)
        request = self._get_mtd_resource(mtd).request()
        yield request
        start_time = env.now + self._proceed_time
        logging.info('MTD: %s deployed in the network at %.1fs.' % (mtd.get_name(), start_time))
        yield env.timeout(exponential_variates(mtd.get_execution_time_mean(),
                                               mtd.get_execution_time_std()))

        # if network is already compromised while executing mtd:
        if self.network.is_compromised(compromised_hosts=self.adversary.get_compromised_hosts()):
            return

        # execute mtd
        mtd.mtd_operation(self.adversary)

        finish_time = env.now + self._proceed_time
        duration = finish_time - start_time
        logging.info('MTD: %s finished in %.1fs at %.1fs.' % (mtd.get_name(), duration, finish_time))
        # release resource
        self._get_mtd_resource(mtd).release(request)
        # append execution records
        self.network.get_mtd_stats().append_mtd_operation_record(mtd, start_time, finish_time, duration)
        # interrupt adversary
        self._interrupt_adversary(env, mtd)

    def _get_mtd_resource(self, mtd):
        """Get the resource to be occupied by the mtd"""
        if mtd.get_resource_type() == 'network':
            return self.network_layer_resource
        elif mtd.get_resource_type() == 'application':
            return self.application_layer_resource
        return self.reserve_resource

    def _interrupt_adversary(self, env, mtd):
        """
        interrupt the attack process of the adversary
        """
        attack_process = self.attack_operation.get_attack_process()
        if attack_process is not None and attack_process.is_alive:
            if mtd.get_resource_type() == 'network':
                self.attack_operation.set_interrupted_mtd(mtd)
                self.attack_operation.get_attack_process().interrupt()
                logging.info(
                    'MTD: Interrupted %s at %.1fs!' % (self.adversary.get_curr_process(),
                                                       env.now + self._proceed_time))
                self.network.get_mtd_stats().append_total_attack_interrupted()
            elif mtd.get_resource_type() == 'application' and \
                    self.adversary.get_curr_process() not in [
                                                            'SCAN_HOST',
                                                            'ENUM_HOST',
                                                            'SCAN_NEIGHBOR']:
                self.attack_operation.set_interrupted_mtd(mtd)
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

