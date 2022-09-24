import simpy
from mtdnetwork.event.time_generator import exponential_variates
from mtdnetwork.stats.attack_stats import AttackStatistics
import logging

HACKER_ATTACK_ATTEMPT_MULTIPLER = 5

SCAN_HOST = 5
ENUM_HOST = 2
SCAN_NEIGHBOR = 5
SCAN_PORT = 10
EXPLOIT_VULN_MEAN = 20
EXPLOIT_VULN_STD = 0.8
BRUTE_FORCE = 20
PENALTY = 2


class Adversary:
    def __init__(self, env, network, attack_threshold):
        self.network = network
        self.compromised_users = []
        self.compromised_hosts = []

        self.host_stack = []

        self.attack_counter = [0 for n in range(self.network.get_total_nodes())]
        self.stop_attack = []
        self.attack_threshold = attack_threshold

        self.pivot_host_id = -1
        self.curr_host_id = -1
        self.curr_host = None
        self.curr_ports = []
        self.curr_vulns = []

        self.max_attack_attempts = HACKER_ATTACK_ATTEMPT_MULTIPLER * network.get_total_nodes()
        self.curr_attempts = 0
        self.target_compromised = False

        self.observed_changes = {}

        # time-based attributes
        self.interrupted_mtd = None
        self.attack_stats = AttackStatistics()
        self.env = env
        self.attack_process = None
        self.curr_process = 'SCAN_HOST'
        self.now = 0

    def proceed_attack(self):
        if self.curr_process == 'SCAN_HOST':
            self.scan_host()
        elif self.curr_process == 'ENUM_HOST':
            self.enum_host()
        elif self.curr_process == 'SCAN_NEIGHBOR':
            self.scan_neighbors()
        elif self.curr_process == 'EXPLOIT_VULN':
            self.exploit_vuln()
        elif self.curr_process == 'BRUTE_FORCE':
            self.brute_force()

    def execute_attack_action(self, time, attack_action):
        """
        a function to execute a given time-consuming attack action
        :param time: The time duration before executing an attack action.
        :param attack_action: attack action
        """
        start_time = self.env.now + self.now
        try:
            logging.info("Adversary: Start %s at %.1fs." % (self.curr_process, start_time))
            yield self.env.timeout(time)
        except simpy.Interrupt:
            self.env.process(self.handling_interruption(start_time, self.curr_process))
            return
        finish_time = self.env.now + self.now
        logging.info("Adversary: Processed %s at %.1fs." % (self.curr_process, finish_time))
        self.attack_stats.append_attack_operation_record(self.curr_process, start_time, finish_time, self)
        attack_action()

    def scan_host(self):
        self.curr_process = 'SCAN_HOST'
        self.attack_process = self.env.process(self.execute_attack_action(SCAN_HOST, self.execute_scan_host))

    def enum_host(self):
        if len(self.host_stack) > 0:
            self.curr_process = 'ENUM_HOST'
            self.attack_process = self.env.process(self.execute_attack_action(ENUM_HOST, self.execute_enum_host))
        else:
            self.scan_host()

    def scan_port(self):
        self.curr_process = 'SCAN_PORT'
        self.attack_process = self.env.process(self.execute_attack_action(SCAN_PORT, self.execute_scan_port))

    def exploit_vuln(self):
        time = exponential_variates(EXPLOIT_VULN_MEAN, EXPLOIT_VULN_STD)
        self.curr_process = 'EXPLOIT_VULN'
        self.attack_process = self.env.process(self.execute_attack_action(time, self.execute_exploit_vuln))

    def brute_force(self):
        self.curr_process = 'BRUTE_FORCE'
        self.attack_process = self.env.process(self.execute_attack_action(BRUTE_FORCE, self.execute_brute_force))

    def scan_neighbors(self):
        self.curr_process = 'SCAN_NEIGHBOR'
        self.attack_process = self.env.process(self.execute_attack_action(SCAN_NEIGHBOR, self.execute_scan_neighbors))

    def execute_scan_host(self):
        """
        Starts the Network enumeration stage.
        Sets up the order of hosts that the hacker will attempt to compromise
        The order is sorted by distance from the exposed endpoints which is done
        in the function adversary.network.host_scan().
        If the scan returns nothing from the scan, then the attacker will stop
        """
        self.pivot_host_id = -1
        self.host_stack = self.network.host_scan(self.compromised_hosts, self.stop_attack)
        if len(self.host_stack) > 0:
            self.enum_host()
        else:
            # terminate the whole process
            return

    def execute_enum_host(self):
        """
        Starts enumerating each host by popping off the host id from the top of the host stack
        time for host hopping required
        Checks if the Hacker has already compromised and backdoored the target host
        """
        self.host_stack = self.network.sort_by_distance_from_exposed_and_pivot_host(
            self.host_stack,
            self.compromised_hosts,
            pivot_host_id=self.pivot_host_id
        )
        self.curr_host_id = self.host_stack.pop(0)
        self.curr_host = self.network.get_host(self.curr_host_id)
        # Sets node as unattackable if has been attack too many times
        self.attack_counter[self.curr_host_id] += 1
        if self.attack_counter[self.curr_host_id] == self.attack_threshold:
            # target node feature
            if self.curr_host_id != self.network.get_target_node():
                self.stop_attack.append(self.curr_host_id)

        # Checks if max attack attempts has been reached, empty stacks if reached
        if self.curr_attempts >= self.max_attack_attempts:
            self.host_stack = []
            return
        self.curr_ports = []
        self.curr_vulns = []

        # Sets the next host that the Hacker will pivot from to compromise other hosts
        # The pivot host needs to be a compromised host that the hacker can access
        self.set_next_pivot_host()

        if self.curr_host.compromised:
            self.update_compromise_progress()
            self.enum_host()
        else:
            # Attack event triggered
            self.scan_port()

    def execute_scan_port(self):
        """
        Starts a port scan on the target host
        Checks if a compromised user has reused their credentials on the target host
        Phase 1
        """
        self.curr_ports = self.curr_host.port_scan()
        user_reuse = self.curr_host.can_auto_compromise_with_users(self.compromised_users)
        if user_reuse:
            self.update_compromise_progress()
            self.scan_neighbors()
            return
        self.exploit_vuln()

    def execute_exploit_vuln(self):
        """
        Finds the top 5 vulnerabilities based on RoA score and have not been exploited yet that the
        Tries exploiting the vulnerabilities to compromise the host
        Checks if the adversary was able to successfully compromise the host
        Phase 2
        """
        self.curr_vulns = self.curr_host.get_vulns(self.curr_ports)
        is_exploited = self.curr_host.exploit_vulns(self.curr_vulns)
        # cumulative vulnerability exploitation attempts
        self.curr_attempts += len(self.curr_vulns)

        for vuln in self.curr_vulns:
            if vuln.is_exploited():
                # todo: record vulnerability roa, impact, and complexity
                # self.scorer.add_vuln_compromise(self.curr_time, vuln)
                pass
        if is_exploited:
            self.update_compromise_progress()
            self.scan_neighbors()
        else:
            self.brute_force()

    def execute_brute_force(self):
        """
        Tries bruteforcing a login for a short period of time using previous passwords from compromised user accounts to guess a new login.
        Checks if credentials for a user account has been successfully compromised.
        Phase 3
        """
        brute_force_result = self.curr_host.compromise_with_users(self.compromised_users)
        if brute_force_result:
            self.update_compromise_progress()
            self.scan_neighbors()
        else:
            self.enum_host()

    def execute_scan_neighbors(self):
        """
        Starts scanning for neighbors from a host that the hacker can pivot to
        Puts the new neighbors discovered to the start of the host stack.
        """
        found_neighbors = self.curr_host.discover_neighbors()
        new_host_stack = found_neighbors + [
            node_id
            for node_id in self.host_stack
            if node_id not in found_neighbors
        ]
        self.host_stack = new_host_stack
        self.enum_host()

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

    def swap_hosts_in_compromised_hosts(self, host_id, other_host_id):
        """
        update compromised host ids for hosttopology shuffle
        """
        new_compromised_hosts = []

        for i in self.compromised_hosts:
            if i == host_id:
                new_compromised_hosts.append(other_host_id)
            elif i == other_host_id:
                new_compromised_hosts.append(host_id)
            else:
                new_compromised_hosts.append(i)

        self.compromised_hosts = new_compromised_hosts

    # def debug_log(self, reason):
    #     """
    #     Debug messages for hosts
    #
    #     Parameters:
    #         reason:
    #             the reason for the debug message
    #     """
    #     self.logger.debug("{}:{}:{}:{}".format(
    #         reason,
    #         self.curr_host.host_id,
    #         self.curr_host.os_type,
    #         self.curr_host.os_version
    #     ))

    # def get_mtd_penality_discount(self, blocked_exceptions):
    #     """
    #     Gets the discount for the MTD blocked action penality depending on how many times the adversary has
    #     seen that change on the network or a host before.
    #
    #     Parameters:
    #         blocked_exceptions:
    #             a list of exceptions that explain what was changed in the network that blocked the action
    #
    #     Returns:
    #         the discount as a decimal to be multiplied with constants.HACKER_BLOCKED_BY_MTD_PENALITY
    #     """
    #     total_observations = 0
    #     total_types_of_changes = len(blocked_exceptions)
    #
    #     for blocked_reason in blocked_exceptions:
    #         total_observations += self.observed_changes.get(blocked_reason, 0)
    #         self.observed_changes[blocked_reason] = self.observed_changes.get(blocked_reason, 0) + 1
    #
    #     average_observations = total_observations / total_types_of_changes
    #
    #     if average_observations > constants.HACKER_BLOCKED_BY_MTD_BLOCKS_TO_MAX_DISCOUNT:
    #         average_observations = constants.HACKER_BLOCKED_BY_MTD_BLOCKS_TO_MAX_DISCOUNT
    #
    #     return 1 - constants.HACKER_BLOCKED_BY_MTD_MAX_DISCOUNT * \
    #            average_observations / constants.HACKER_BLOCKED_BY_MTD_BLOCKS_TO_MAX_DISCOUNT
    def handling_interruption(self, start_time, name):
        """
        a function to handle the interruption of the attack action caused by MTD operations
        :param start_time: the start time of the attack action
        :param name: the name of the attack action
        """
        self.attack_stats.append_attack_operation_record(name, start_time, self.env.now + self.now, self)
        # confusion penalty caused by MTD operation
        yield self.env.timeout(PENALTY)

        if self.interrupted_mtd.resource_type == 'network':
            self.interrupted_mtd = None
            self.curr_host_id = -1
            self.curr_host = None
            logging.info('Adversary: Restarting with SCAN_HOST at %.1fs!' % (self.env.now + self.now))
            self.scan_host()
        elif self.interrupted_mtd.resource_type == 'application':
            self.interrupted_mtd = None
            logging.info('Adversary: Restarting with SCAN_PORT at %.1fs!' % (self.env.now + self.now))
            self.scan_port()

    def update_compromise_progress(self):
        """
        Updates the Hackers progress state when it compromises a host.
        """
        self.pivot_host_id = self.curr_host_id
        if self.curr_host_id not in self.compromised_hosts:
            self.compromised_hosts.append(self.curr_host_id)
            self.attack_stats.update_compromise_host(self.curr_host_id)
            logging.info("Adversary: Host %i has been compromised at %.1fs!" % (self.curr_host_id, self.env.now+self.now))
            self.network.update_reachable_compromise(self.curr_host_id, self.compromised_hosts)

            for user in self.curr_host.get_compromised_users():
                if user not in self.compromised_users:
                    self.attack_stats.update_compromise_user(user)
            self.compromised_users = list(set(self.compromised_users + self.curr_host.get_compromised_users()))
            if self.network.is_compromised(self.compromised_hosts):
                # terminate the whole process
                return

            # If target network, set adversary as done once adversary has compromised target node
            # if self.network.get_target_node() == self.curr_host_id:
            # if self.network.get_network_type() == 0:
            #      # terminate the whole process
            #     self.target_compromised = True
            #     self.end_event.succeed()
            #     return
            #

    def get_compromised_hosts(self):
        return self.compromised_hosts

    def get_statistics(self):
        return self.attack_stats.get_record()

    def clear_properties(self):
        self.env = None
        self.interrupted_mtd = None
        self.attack_process = None
        return self

    def reconfigure_properties(self, env, now):
        self.env = env
        self.now = now
