from mtdnetwork.mtd import *

class UserShuffle(MTD):
    def __init__(self, network):
        self.logger = logging.getLogger("mtd:usershuffle")
        super().__init__("UserShuffle", network)

    def mtd_operation(self):
        self.logger.info("changing users on hosts")
        hosts = self.network.get_hosts()

        for host_instance in hosts.values():
            host_instance.set_host_users(
                random.choices(
                    self.network.users_list, 
                    k=self.network.users_per_host
                )
            )