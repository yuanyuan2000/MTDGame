import simpy
from mtdnetwork.network.hacker import Hacker
from mtdnetwork.event.time_generator import exponential_variates
from mtdnetwork.stats.attack_stats import AttackStatistics
import logging

SCAN_HOST = 5
ENUM_HOST = 2
SCAN_NEIGHBOR = 5
SCAN_PORT = 10
EXPLOIT_VULN_MEAN = 30
EXPLOIT_VULN_STD = 0.8
BRUTE_FORCE = 20
PENALTY = 2


class Adversary(Hacker):
    def __init__(self, env, network, attack_threshold):
        super().__init__(network, attack_threshold)
        self.interrupted_mtd = None
        self.attack_stats = AttackStatistics()
        self.env = env
        self.attack_process = None
        self.curr_process = 'SCAN_HOST'
        self.end_event = self.env.event()

        # start attack!
        self.scan_host()

    def execute_attack_action(self, time, attack_action):
        """
        a function to execute a given time-consuming attack action
        :param time: The time duration before executing an attack action.
        :param attack_action: attack action
        """
        start_time = self.env.now
        try:
            logging.info("Adversary: Start %s at %.1fs." % (self.curr_process, start_time))
            yield self.env.timeout(time)
        except simpy.Interrupt:
            self.env.process(self.handling_interruption(start_time, self.curr_process))
            return
        finish_time = self.env.now
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

    def handling_interruption(self, start_time, name):
        """
        a function to handle the interruption of the attack action caused by MTD operations
        :param start_time: the start time of the attack action
        :param name: the name of the attack action
        """
        self.attack_stats.append_attack_operation_record(name, start_time, self.env.now, self)
        # confusion penalty caused by MTD operation
        yield self.env.timeout(PENALTY)

        if self.interrupted_mtd.resource_type == 'network':
            self.reset_interrupt_state()
            self.reset_host_state()
            logging.info('Adversary: Restarting with host scan operation!')
            self.scan_host()
        elif self.interrupted_mtd.resource_type == 'application':
            self.reset_interrupt_state()
            logging.info('Adversary: Restarting with host scan operation!')
            self.scan_port()

    def reset_interrupt_state(self):
        self.interrupted_mtd = None

    def reset_host_state(self):
        self.curr_host_id = -1
        self.curr_host = None

    def update_compromise_progress(self):
        """
        Updates the Hackers progress state when it compromises a host.
        """
        self.pivot_host_id = self.curr_host_id
        if self.curr_host_id not in self.compromised_hosts:
            self.compromised_hosts.append(self.curr_host_id)
            self.attack_stats.update_compromise_host(self.curr_host_id)
            logging.info("Adversary: Host %i has been compromised at %.1fs!: " % (self.curr_host_id, self.env.now))
            self.network.update_reachable_compromise(self.curr_host_id, self.compromised_hosts)

            for user in self.curr_host.get_compromised_users():
                if user not in self.compromised_users:
                    # self.scorer.add_user_account_leak(self.curr_time, user)
                    pass
            self.compromised_users = list(set(self.compromised_users + self.curr_host.get_compromised_users()))
            if self.network.is_compromised(self.compromised_hosts):
                # terminate the whole process todo
                return

            # If target network, set adversary as done once adversary has compromised target node
            # if self.network.get_target_node() == self.curr_host_id:
            # if self.network.get_network_type() == 0:
            #      # terminate the whole process todo
            #     self.target_compromised = True
            #     self.end_event.succeed()
            #     return
            #

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
            # terminate the whole process todo
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
            self.done = True
        self.curr_ports = []
        self.curr_vulns = []
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
            # self.scorer.add_host_reuse_pass_compromise(self.curr_time, self.curr_host)
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
                # self.scorer.add_vuln_compromise(self.curr_time, vuln)
                pass
        if is_exploited:
            self.update_compromise_progress()
            # self.scorer.add_host_vuln_compromise(self.curr_time, self.curr_host)
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
            # self.scorer.add_host_pass_spray_compromise(self.curr_time, self.curr_host)
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
