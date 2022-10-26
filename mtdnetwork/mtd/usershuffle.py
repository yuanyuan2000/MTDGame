from mtdnetwork.mtd import MTD
import random


class UserShuffle(MTD):
    def __init__(self, network, priority=7):
        super().__init__(name="UserShuffle",
                         mtd_type='shuffle',
                         resource_type='reserve',
                         execution_time_mean=40,
                         execution_time_std=0.5,
                         priority=priority,
                         network=network)

    def mtd_operation(self, adversary=None):
        hosts = self.network.get_hosts()

        for host_instance in hosts.values():
            host_instance.set_host_users(
                random.choices(
                    self.network.users_list,
                    k=self.network.users_per_host
                )
            )
