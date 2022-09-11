import logging

import mtdnetwork.constants as constants


class Hacker:

    def __init__(self, network, attack_threshold):
        """
        Creates an instance of the Hacker that is trying to penetrate the network

        Parameters:
            network:
                the Network instance that this hacker is trying to compromise
            attack_threshold:
                the number of attempts an attacker would attempt to attack a host before giving up
        """
        self.network = network
        self.scorer = self.network.get_scorer()
        self.compromised_users = []
        self.compromised_hosts = []

        self.host_stack = []
        self.seen = []
        self.done = False

        self.attack_counter = [0 for n in range(self.network.get_total_nodes())]
        self.stop_attack = []
        self.attack_threshold = attack_threshold

        self.curr_time = 0

        self.pivot_host_id = -1
        self.curr_host_id = -1
        self.curr_host = None
        self.curr_ports = []
        self.curr_vulns = []

        self.total_vuln_compromise = 0
        self.total_reuse_pass_compromise = 0
        self.total_brute_force_compromise = 0
        self.total_blocked_by_mtd = 0
        self.max_attack_attempts = constants.HACKER_ATTACK_ATTEMPT_MULTIPLER * network.get_total_nodes()
        self.curr_attempts = 0
        self.target_compromised = False

        self.logger = logging.getLogger(__name__)

        self.observed_changes = {}

    def swap_hosts_in_compromised_hosts(self, host_id, other_host_id):
        new_compromised_hosts = []

        for id in self.compromised_hosts:
            if id == host_id:
                new_compromised_hosts.append(other_host_id)
            elif id == other_host_id:
                new_compromised_hosts.append(host_id)
            else:
                new_compromised_hosts.append(id)

        self.compromised_hosts = new_compromised_hosts

    def remove_host_id_from_compromised(self, host_id):
        self.compromised_hosts = [
            id
            for id in self.compromised_hosts
            if id != host_id
        ]

    def get_statistics(self):
        """
        Returns statistics for the simulation
        """

        return {
            "Total Host Compromises": len(self.compromised_hosts),
            "Total User Compromises": len(self.compromised_users),
            "Total Vuln Compromises": self.total_vuln_compromise,
            "Total Attack Attempts": self.curr_attempts,
            "Total Reuse Pass Compromises": self.total_reuse_pass_compromise,
            "Total Password Spray Compromises": self.total_brute_force_compromise,
            "Total Actions Blocked by MTD": self.total_blocked_by_mtd,
            "Target Node Compromised": self.target_compromised,
            "Compromised hosts": self.compromised_hosts,
            "Average Attempts Required to Compromise": self.attacks_required_per_compromise()[0],
            "Number of Hosts Attacker has given up on": len(self.stop_attack)
        }

    def get_compromised(self):
        """
        Returns a list of compromised nodes
        """
        return self.compromised_hosts

    def get_stop_attack(self):
        """
        Returns a list of compromised nodes
        """
        return self.stop_attack

    def get_attack_attempts(self):
        """
        Returns the number of attack attempts
        """
        return self.curr_attempts

    def log_host_result(self, reason):
        """
        Logs a result for a compromising a particular host

        Parameters:
            reason:
                the reason the host got compromised
        """
        self.logger.debug("{}:{}:{}:{}".format(
            reason,
            self.curr_host.host_id,
            self.curr_host.os_type,
            self.curr_host.os_version
        ))

    def debug_log(self, reason):
        """
        Debug messages for hosts

        Parameters:
            reason:
                the reason for the debug message
        """
        self.logger.debug("{}:{}:{}:{}".format(
            reason,
            self.curr_host.host_id,
            self.curr_host.os_type,
            self.curr_host.os_version
        ))

    def set_next_pivot_host(self):
        """
        Sets the next host that the Hacker will pivot from to compromise other hosts

        The pivot host needs to be a compromised host that the hacker can access
        """
        neighbors = list(self.network.get_neighbors(self.curr_host_id))
        if self.pivot_host_id in neighbors:
            return

        for n in neighbors:
            if n in self.compromised_hosts:
                self.pivot_host_id = n
                return

        self.pivot_host_id = -1

    def get_mtd_penality_discount(self, blocked_exceptions):
        """
        Gets the discount for the MTD blocked action penality depending on how many times the adversary has 
        seen that change on the network or a host before.

        Parameters:
            blocked_exceptions:
                a list of exceptions that explain what was changed in the network that blocked the action

        Returns:
            the discount as a decimal to be multiplied with constants.HACKER_BLOCKED_BY_MTD_PENALITY
        """
        total_observations = 0
        total_types_of_changes = len(blocked_exceptions)

        for blocked_reason in blocked_exceptions:
            total_observations += self.observed_changes.get(blocked_reason, 0)
            self.observed_changes[blocked_reason] = self.observed_changes.get(blocked_reason, 0) + 1

        average_observations = total_observations / total_types_of_changes

        if average_observations > constants.HACKER_BLOCKED_BY_MTD_BLOCKS_TO_MAX_DISCOUNT:
            average_observations = constants.HACKER_BLOCKED_BY_MTD_BLOCKS_TO_MAX_DISCOUNT

        return 1 - constants.HACKER_BLOCKED_BY_MTD_MAX_DISCOUNT * \
               average_observations / constants.HACKER_BLOCKED_BY_MTD_BLOCKS_TO_MAX_DISCOUNT

    def attacks_required_per_compromise(self):
        """
        Checks the amount of attempts required per compromise

        Returns:
            ave_attempts: Average number of attacks required to compromise a host
            return_list: List of all compromised hosts and number of attempts required to compromise
        """

        return_list = []
        total_attempts = 0
        i = 0
        for host_id in self.compromised_hosts:
            append_list = [self.compromised_hosts[i], self.attack_counter[host_id]]
            i += 1
            total_attempts += self.attack_counter[host_id]
            return_list.append(append_list)
        ave_attempts = total_attempts / len(self.compromised_hosts)

        return ave_attempts, return_list

    def update_progress_state(self):
        """
        Updates the Hackers progress state when it compromises a host.
        """

        if not self.curr_host_id in self.compromised_hosts:
            self.compromised_hosts.append(self.curr_host_id)
            print("This host has been compromised: ", self.curr_host_id)
            self.network.update_reachable_compromise(self.curr_host_id, self.compromised_hosts)
            for user in self.curr_host.get_compromised_users():
                if not user in self.compromised_users:
                    self.scorer.add_user_account_leak(self.curr_time, user)
            self.compromised_users = list(set(self.compromised_users + self.curr_host.get_compromised_users()))
            if self.network.is_compromised(self.compromised_hosts):
                self.done = True
            # If target network, set adversary as done once adversary has compromised target node 
            if self.network.get_target_node() in self.compromised_hosts:
                if self.network.get_network_type() == 0:
                    self.target_compromised = True
                    self.done = True
