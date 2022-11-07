from mtdnetwork.mtd.completetopologyshuffle import CompleteTopologyShuffle
from mtdnetwork.mtd.ipshuffle import IPShuffle
from mtdnetwork.mtd.hosttopologyshuffle import HostTopologyShuffle
from mtdnetwork.mtd.portshuffle import PortShuffle
from mtdnetwork.mtd.osdiversity import OSDiversity
from mtdnetwork.mtd.servicediversity import ServiceDiversity
from mtdnetwork.mtd.usershuffle import UserShuffle
from mtdnetwork.data.constants import MTD_TRIGGER_INTERVAL
import random


class MTDScheme:

    def __init__(self, scheme: str, network):
        self._scheme = scheme
        self._mtd_trigger_interval = None
        self._mtd_trigger_std = None
        self._mtd_register_scheme = None
        self._mtd_strategies = [CompleteTopologyShuffle, IPShuffle, HostTopologyShuffle, UserShuffle,
                                PortShuffle, OSDiversity, ServiceDiversity]
        self.network = network
        self._init_mtd_scheme(scheme)

    def _init_mtd_scheme(self, scheme):
        """
        assign an MTD scheme based on the parameter
        """
        self._mtd_trigger_interval, self._mtd_trigger_std = MTD_TRIGGER_INTERVAL[scheme]
        if scheme == 'simultaneously':
            self._mtd_register_scheme = self._register_mtd_simultaneously
        elif scheme == 'randomly':
            self._mtd_register_scheme = self._register_mtd_randomly
        elif scheme == 'alternatively':
            self._mtd_register_scheme = self._register_mtd_alternatively

    def _mtd_register(self, mtd):
        """
        register an MTD strategy to the queue
        """
        mtd_strategy = mtd(network=self.network)
        self.network.get_mtd_queue().put((mtd_strategy.get_priority(), mtd_strategy))

    def _register_mtd_simultaneously(self):
        """
        register all MTDs for simultaneous scheme
        """
        for mtd in self._mtd_strategies:
            self._mtd_register(mtd=mtd)
        return self.network.get_mtd_queue()

    def _register_mtd_randomly(self):
        """
        register an MTD for random scheme
        """
        self._mtd_register(mtd=random.choice(self._mtd_strategies))

    def _register_mtd_alternatively(self):
        """
        register an MTD for alternative scheme
        todo: dynamic MTDs based on the network state
        """
        self.network.get_unfinished_mtd()

        pass

    def trigger_suspended_mtd(self):
        """
        trigger an MTD from suspended list
        """
        suspend_dict = self.network.get_suspended_mtd()
        mtd = suspend_dict[min(suspend_dict.keys())]
        del suspend_dict[min(suspend_dict.keys())]
        return mtd

    def trigger_mtd(self):
        """
        trigger an MTD from mtd queue
        """
        return self.network.get_mtd_queue().get()[1]

    def suspend_mtd(self, mtd_strategy):
        """
        put an MTD into the suspended list
        """
        self.network.get_mtd_stats().append_total_suspended()
        self.network.get_suspended_mtd()[mtd_strategy.get_priority()] = mtd_strategy

    def register_mtd(self):
        """
        call an MTD register scheme function
        """
        self._mtd_register_scheme()

    def get_scheme(self):
        return self._scheme

    def get_mtd_trigger_interval(self):
        return self._mtd_trigger_interval

    def get_mtd_trigger_std(self):
        return self._mtd_trigger_std
