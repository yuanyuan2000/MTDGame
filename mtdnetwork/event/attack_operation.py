import simpy
from mtdnetwork.event.time_generator import exponential_variates
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


class AttackOperation:
    def __init__(self, env, adversary):
        self.env = env
        self.adversary = adversary
        self._attack_process = None
        self._interrupted_mtd = None
        self._proceed_time = 0

    def proceed_attack(self):
        if self.adversary.get_curr_process() == 'SCAN_HOST':
            self.scan_host()
        elif self.adversary.get_curr_process() == 'ENUM_HOST':
            self.enum_host()
        elif self.adversary.get_curr_process() == 'SCAN_PORT':
            self.scan_port()
        elif self.adversary.get_curr_process() == 'SCAN_NEIGHBOR':
            self.scan_neighbors()
        elif self.adversary.get_curr_process() == 'EXPLOIT_VULN':
            self.exploit_vuln()
        elif self.adversary.get_curr_process() == 'BRUTE_FORCE':
            self.brute_force()

    def execute_attack_action(self, time, attack_action):
        """
        a function to execute a given time-consuming attack action
        :param time: The time duration before executing an attack action.
        :param attack_action: attack action
        """
        start_time = self.env.now + self._proceed_time
        try:
            logging.info("Adversary: Start %s at %.1fs." % (self.adversary.get_curr_process(), start_time))
            yield self.env.timeout(time)
        except simpy.Interrupt:
            self.env.process(self.handle_interrupt(start_time, self.adversary.get_curr_process()))
            return
        finish_time = self.env.now + self._proceed_time
        logging.info("Adversary: Processed %s at %.1fs." % (self.adversary.get_curr_process(), finish_time))
        self.adversary.get_attack_stats().append_attack_operation_record(self.adversary.get_curr_process(), start_time,
                                                                         finish_time, self.adversary)
        attack_action()

    def scan_host(self):
        self.adversary.set_curr_process('SCAN_HOST')
        self._attack_process = self.env.process(self.execute_attack_action(SCAN_HOST,
                                                                           self.execute_scan_host))

    def enum_host(self):
        if len(self.adversary.get_host_stack()) > 0:
            self.adversary.set_curr_process('ENUM_HOST')
            self._attack_process = self.env.process(self.execute_attack_action(ENUM_HOST,
                                                                               self.execute_enum_host))
        else:
            self.scan_host()

    def scan_port(self):
        self.adversary.set_curr_process('SCAN_PORT')
        self._attack_process = self.env.process(self.execute_attack_action(SCAN_PORT,
                                                                           self.execute_scan_port))

    def exploit_vuln(self):
        exploit_time = exponential_variates(EXPLOIT_VULN_MEAN, EXPLOIT_VULN_STD)
        self.adversary.set_curr_process('EXPLOIT_VULN')
        self._attack_process = self.env.process(self.execute_attack_action(exploit_time,
                                                                           self.execute_exploit_vuln))

    def brute_force(self):
        self.adversary.set_curr_process('BRUTE_FORCE')
        self._attack_process = self.env.process(self.execute_attack_action(BRUTE_FORCE,
                                                                           self.execute_brute_force))

    def scan_neighbors(self):
        self.adversary.set_curr_process('SCAN_NEIGHBOR')
        self._attack_process = self.env.process(self.execute_attack_action(SCAN_NEIGHBOR,
                                                                           self.execute_scan_neighbors))

    def handle_interrupt(self, start_time, name):
        """
        a function to handle the interrupt of the attack action caused by MTD operations
        :param start_time: the start time of the attack action
        :param name: the name of the attack action
        """
        self.adversary.get_attack_stats().append_attack_operation_record(name, start_time,
                                                                         self.env.now + self._proceed_time,
                                                                         self.adversary, self._interrupted_mtd, )
        # confusion penalty caused by MTD operation
        yield self.env.timeout(PENALTY)

        if self._interrupted_mtd.get_resource_type() == 'network':
            self._interrupted_mtd = None
            self.adversary.set_curr_host_id(-1)
            self.adversary.set_curr_host(None)
            logging.info('Adversary: Restarting with SCAN_HOST at %.1fs!' % (self.env.now + self._proceed_time))
            self.scan_host()
        elif self._interrupted_mtd.get_resource_type() == 'application':
            self._interrupted_mtd = None
            logging.info('Adversary: Restarting with SCAN_PORT at %.1fs!' % (self.env.now + self._proceed_time))
            self.scan_port()

    def execute_scan_host(self):
        """
        Starts the Network enumeration stage.
        Sets up the order of hosts that the hacker will attempt to compromise
        The order is sorted by distance from the exposed endpoints which is done
        in the function adversary.network.host_scan().
        If the scan returns nothing from the scan, then the attacker will stop
        """
        self.adversary.set_pivot_host_id(-1)
        self.adversary.set_host_stack(self.adversary.get_network().host_scan(self.adversary.get_compromised_hosts(),
                                                                             self.adversary.get_stop_attack()))
        if len(self.adversary.get_host_stack()) > 0:
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
        self.adversary.set_host_stack(self.adversary.get_network().sort_by_distance_from_exposed_and_pivot_host(
            self.adversary.get_host_stack(),
            self.adversary.get_compromised_hosts(),
            pivot_host_id=self.adversary.get_pivot_host_id()
        ))
        self.adversary.set_curr_host_id(self.adversary.get_host_stack().pop(0))
        self.adversary.set_curr_host(self.adversary.get_network().get_host(self.adversary.get_curr_host_id()))
        # Sets node as unattackable if has been attack too many times
        self.adversary.get_attack_counter()[self.adversary.get_curr_host_id()] += 1
        if self.adversary.get_attack_counter()[self.adversary.get_curr_host_id()] == self.adversary.get_attack_threshold():
            # target node feature
            if self.adversary.get_curr_host_id() != self.adversary.get_network().get_target_node():
                self.adversary.get_stop_attack().append(self.adversary.get_curr_host_id())

        # Checks if max attack attempts has been reached, empty stacks if reached
        if self.adversary.get_curr_attempts() >= self.adversary.get_max_attack_attempts():
            self.adversary.set_host_stack([])
            return
        self.adversary.set_curr_ports([])
        self.adversary.set_curr_vulns([])

        # Sets the next host that the Hacker will pivot from to compromise other hosts
        # The pivot host needs to be a compromised host that the hacker can access
        self.set_next_pivot_host()

        if self.adversary.get_curr_host().compromised:
            self.adversary.update_compromise_progress(self.env.now, self._proceed_time)
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
        self.adversary.set_curr_ports(self.adversary.get_curr_host().port_scan())
        user_reuse = self.adversary.get_curr_host().can_auto_compromise_with_users(
            self.adversary.get_compromised_users())
        if user_reuse:
            self.adversary.update_compromise_progress(self.env.now, self._proceed_time)
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
        self.adversary.set_curr_vulns(self.adversary.get_curr_host().get_vulns(self.adversary.get_curr_ports()))
        is_exploited = self.adversary.get_curr_host().exploit_vulns(self.adversary.get_curr_vulns())
        # cumulative vulnerability exploitation attempts
        self.adversary.set_curr_attempts(self.adversary.get_curr_attempts() + len(self.adversary.get_curr_vulns()))

        for vuln in self.adversary.get_curr_vulns():
            if vuln.is_exploited():
                # todo: record vulnerability roa, impact, and complexity
                # self.scorer.add_vuln_compromise(self.curr_time, vuln)
                pass
        if is_exploited:
            self.adversary.update_compromise_progress(self.env.now, self._proceed_time)
            self.scan_neighbors()
        else:
            self.brute_force()

    def execute_brute_force(self):
        """
        Tries bruteforcing a login for a short period of time using previous passwords from compromised user accounts to guess a new login.
        Checks if credentials for a user account has been successfully compromised.
        Phase 3
        """
        brute_force_result = self.adversary.get_curr_host().compromise_with_users(
            self.adversary.get_compromised_users())
        if brute_force_result:
            self.adversary.update_compromise_progress(self.env.now, self._proceed_time)
            self.scan_neighbors()
        else:
            self.enum_host()

    def execute_scan_neighbors(self):
        """
        Starts scanning for neighbors from a host that the hacker can pivot to
        Puts the new neighbors discovered to the start of the host stack.
        """
        found_neighbors = self.adversary.get_curr_host().discover_neighbors()
        new__host_stack = found_neighbors + [
            node_id
            for node_id in self.adversary.get_host_stack()
            if node_id not in found_neighbors
        ]
        self.adversary.set_host_stack(new__host_stack)
        self.enum_host()

    def set_next_pivot_host(self):
        """
        Sets the next host that the Hacker will pivot from to compromise other hosts
        The pivot host needs to be a compromised host that the hacker can access
        """
        neighbors = list(self.adversary.get_network().get_neighbors(self.adversary.get_curr_host_id()))
        if self.adversary.get_pivot_host_id() in neighbors:
            return
        for n in neighbors:
            if n in self.adversary.get_compromised_hosts():
                self.adversary.set_pivot_host_id(n)
                return
        self.adversary.set_pivot_host_id(-1)

    def get_proceed_time(self):
        return self._proceed_time

    def set_proceed_time(self, proceed_time):
        self._proceed_time = proceed_time

    def get_attack_process(self):
        return self._attack_process

    def set_attack_process(self, attack_process):
        self._attack_process = attack_process

    def set_interrupted_mtd(self, mtd):
        self._interrupted_mtd = mtd
