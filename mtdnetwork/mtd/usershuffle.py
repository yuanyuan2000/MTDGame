from mtdnetwork.mtd import *


class UserShuffle(MTD):
    def __init__(self, network, mtd_operation):
        self.logger = logging.getLogger("mtd:usershuffle")
        super().__init__(name="UserShuffle", network=network, resource_type='reserve',
                         resource=mtd_operation.get_reserve_resource(), execution_time_mean=10, execution_time_std=0.5)

    def mtd_operation(self, adversary=None):
        self.logger.debug("changing users on hosts")
        hosts = self.network.get_hosts()

        for host_instance in hosts.values():
            host_instance.set_host_users(
                random.choices(
                    self.network.users_list,
                    k=self.network.users_per_host
                )
            )
