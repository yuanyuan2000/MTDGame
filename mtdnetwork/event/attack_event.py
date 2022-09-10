import simpy

from mtdnetwork.network.hacker import Hacker
from mtdnetwork.event.time_generator import exponential_variates

HOST_SCAN = 5
HOST_ENUM = 5
SCAN_NEIGHBOUR = 0
PORT_SCAN = 10
EXPLOIT_VULN_MEAN = 30
EXPLOIT_VULN_STD = 0.8
BRUTE_FORCE = 20
PENALTY = 2


class Adversary(Hacker):
    def __init__(self, env, network, attack_threshold, attack_operation_record):
        super().__init__(network, attack_threshold)
        self.interrupted_by = ''
        self.interrupted_in = ''
        self.attack_operation_record = attack_operation_record
        self.env = env
        self.attack_process = env.process(self.host_scan_and_setup_host_enum(env))
        self.curr_process = 'host_scan'

    def host_scan_and_setup_host_enum(self, env):
        """
        Starts the Network enumeration stage.

        Sets up the order of hosts that the hacker will attempt to compromise

        The order is sorted by distance from the exposed endpoints which is done
        in the function adversary.network.host_scan().

        If the scan returns nothing from the scan, then the attacker will stop
        """

        start_time = env.now
        try:
            print("Adversary: Start Host Scan at %.1fs." % start_time)
            yield env.timeout(HOST_SCAN)
        except simpy.Interrupt:
            env.process(self.handling_interruption(env, start_time, 'HostScan'))
            return
        finish_time = env.now
        print("Adversary: Processed host scan at %.1fs." % finish_time)
        self.handle_attack_operation_record('HostScan', start_time, finish_time)

        self.pivot_host_id = -1
        self.host_stack = self.network.host_scan(self.compromised_hosts, self.stop_attack)

        # print("Adversary: Processed host scan at %.1fs." % env.now)
        if len(self.host_stack) > 0:
            self.attack_process = env.process(self.start_host_enumeration(env))
            self.curr_process = 'host_enum'
        else:
            # terminate the whole process
            self.done = True

    def start_host_enumeration(self, env):
        """
        Starts enumerating each host by popping off the host id from the top of the host stack
        time for host hopping required
        Checks if the Hacker has already compromised and backdoored the target host
        """
        start_time = env.now
        try:
            print("Adversary: Start Host Enum at %.1fs." % start_time)
            yield env.timeout(HOST_ENUM)
        except simpy.Interrupt:
            env.process(self.handling_interruption(env, start_time, 'HostEnum'))
            return
        finish_time = env.now
        print("Adversary: Processed host enum at %.1fs." % finish_time)
        self.handle_attack_operation_record('HostEnum', start_time, finish_time)

        if len(self.host_stack) > 0:
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
                # if self.curr_host_id != self.network.get_target_node():
                self.stop_attack.append(self.curr_host_id)

            # Checks if max attack attempts has been reached, empty stacks if reached
            if self.curr_attempts >= self.max_attack_attempts:
                self.host_stack = []
                self.done = True
                # Debugging attack attempts
            # if self.curr_attempts % 50 == 0:
            #     print("Adversary: Current attack attempts: ", self.curr_attempts)

            self.curr_ports = []
            self.curr_vulns = []
            self.set_next_pivot_host()
            # print("Adversary: Processed host enum at %.1fs." % env.now)
            already_compromised = self.curr_host.compromised
            if already_compromised:
                self.update_progress_state_info(env.now)
                self.pivot_host_id = self.curr_host_id
                self.attack_process = env.process(self.start_host_enumeration(env))
                self.curr_process = 'host_enum'
            else:
                # Attack event triggered
                self.attack_process = env.process(self.start_and_process_port_scan(env))
                self.curr_process = 'port_scan'
        else:
            self.attack_process = env.process(self.host_scan_and_setup_host_enum(env))
            self.curr_process = 'host_scan'

    def start_and_process_port_scan(self, env):
        """
        Starts a port scan on the target host
        Checks if a compromised user has reused their credentials on the target host
        Phase 1
        """
        start_time = env.now
        try:
            print("Adversary: Start port scan at %.1fs." % start_time)
            yield env.timeout(PORT_SCAN)
        except simpy.Interrupt:
            env.process(self.handling_interruption(env, start_time, 'PortScan'))
            return
        finish_time = env.now
        print("Adversary: Processed port scan at %.1fs." % finish_time)
        self.handle_attack_operation_record('PortScan', start_time, finish_time)

        self.curr_ports = self.curr_host.port_scan()
        user_reuse = self.curr_host.can_auto_compromise_with_users(self.compromised_users)
        if user_reuse:
            self.update_progress_state_info(env.now)
            self.pivot_host_id = self.curr_host_id
            self.total_reuse_pass_compromise += 1
            # self.scorer.add_host_reuse_pass_compromise(self.curr_time, self.curr_host)
            self.attack_process = env.process(self.scan_and_setup_new_neighbors(env))
            self.curr_process = 'neighbor_scan'
            return

        self.attack_process = env.process(self.find_and_exploit_vulns(env))
        self.curr_process = 'vulnerability_exploit'

    def find_and_exploit_vulns(self, env):
        """
        Finds the top 5 vulnerabilities based on RoA score and have not been exploited yet that the
        Tries exploiting the vulnerabilities to compromise the host
        Checks if the adversary was able to successfully compromise the host
        Phase 2
        """
        start_time = env.now
        try:
            print("Adversary: Start vulnerability exploitation at %.1fs." % start_time)
            yield env.timeout(exponential_variates(EXPLOIT_VULN_MEAN, EXPLOIT_VULN_STD))
        except simpy.Interrupt:
            env.process(self.handling_interruption(env, start_time, 'VulnerabilityExploit'))
            return
        print('Adversary: Processed vulnerabilities exploitation at %.1fs' % env.now)
        finish_time = env.now
        self.handle_attack_operation_record('VulnerabilityExploit', start_time, finish_time)
        self.curr_vulns = self.curr_host.get_vulns(self.curr_ports)
        is_exploited = self.curr_host.exploit_vulns(self.curr_vulns)
        self.curr_attempts += len(self.curr_vulns)

        for vuln in self.curr_vulns:
            if vuln.is_exploited():
                # self.scorer.add_vuln_compromise(self.curr_time, vuln)
                pass
        if is_exploited:
            self.update_progress_state_info(env.now)
            self.pivot_host_id = self.curr_host_id
            self.total_vuln_compromise += 1
            # self.scorer.add_host_vuln_compromise(self.curr_time, self.curr_host)
            self.attack_process = env.process(self.scan_and_setup_new_neighbors(env))
            self.curr_process = 'neighbor_scan'
        else:
            self.attack_process = env.process(self.brute_force_users_login(env))
            self.curr_process = 'brute_force'

    def brute_force_users_login(self, env):
        """
        Tries bruteforcing a login for a short period of time using previous passwords from compromised user accounts to guess a new login.
        Checks if credentials for a user account has been successfully compromised.
        Phase 3
        """
        start_time = env.now
        try:
            print("Adversary: Start brute force at %.1fs." % start_time)
            yield env.timeout(BRUTE_FORCE)
        except simpy.Interrupt:
            env.process(self.handling_interruption(env, start_time, 'BruteForce'))
            return
        finish_time = env.now
        print('Adversary: Processed brute force user at %.1fs.' % finish_time)
        self.handle_attack_operation_record('BruteForce', start_time, finish_time)

        brute_force_result = self.curr_host.compromise_with_users(self.compromised_users)
        if brute_force_result:
            self.update_progress_state_info(env.now)
            self.pivot_host_id = self.curr_host_id
            self.total_brute_force_compromise += 1
            # self.scorer.add_host_pass_spray_compromise(self.curr_time, self.curr_host)
            self.attack_process = env.process(self.scan_and_setup_new_neighbors(env))
            self.curr_process = 'neighbor_scan'
        else:
            self.attack_process = env.process(self.start_host_enumeration(env))
            self.curr_process = 'host_enum'

    def scan_and_setup_new_neighbors(self, env):
        """
        Starts scanning for neighbors from a host that the hacker can pivot to
        Puts the new neighbors discovered to the start of the host stack.
        """
        yield env.timeout(SCAN_NEIGHBOUR)
        # print('Adversary: Processed scan neighbour at %.1f.' % env.now)
        found_neighbors = self.curr_host.discover_neighbors()
        new_host_stack = found_neighbors + [
            node_id
            for node_id in self.host_stack
            if node_id not in found_neighbors
        ]
        self.host_stack = new_host_stack
        self.attack_process = env.process(self.start_host_enumeration(env))
        self.curr_process = 'host_enum'

    def handling_interruption(self, env, start_time, name):
        self.handle_attack_operation_record(name, start_time, env.now)

        # confusion penalty caused by MTD operation
        yield env.timeout(PENALTY)

        if self.interrupted_in == 'Network Layer' or self.curr_process == 'host_enum' or self.curr_process == 'host_scan':
            self.reset_interrupt_state()
            print('Adversary: Restarting with host scan operation!')
            self.attack_process = env.process(self.host_scan_and_setup_host_enum(env))
            self.curr_process = 'host_scan'
        elif self.interrupted_in == 'Application Layer':
            self.reset_interrupt_state()
            print('Adversary: Restarting with port scan operation!')
            self.attack_process = env.process(self.start_and_process_port_scan(env))
            self.curr_process = 'port_scan'

    def reset_interrupt_state(self):
        self.interrupted_in = ''
        self.interrupted_by = ''

    def handle_attack_operation_record(self, name, start_time, finish_time):

        duration = finish_time - start_time
        self.attack_operation_record.append({
            'name': name,
            'start_time': start_time,
            'finish_time': finish_time,
            'duration': duration,
            'interrupted_in': self.interrupted_in,
            'interrupted_by': self.interrupted_by,
            'compromise_host': ''
        })

    def update_progress_state_info(self, compromised_time):
        """
        Updates the Hackers progress state when it compromises a host.
        """
        if self.curr_host_id not in self.compromised_hosts:
            self.compromised_hosts.append(self.curr_host_id)
            self.attack_operation_record[-1]['compromise_host'] = self.curr_host_id
            print("Adversary: Host %i has been compromised at %.1fs!: " % (self.curr_host_id, compromised_time))
            self.network.update_reachable_compromise(self.curr_host_id, self.compromised_hosts)
            for user in self.curr_host.get_compromised_users():
                if user not in self.compromised_users:
                    # self.scorer.add_user_account_leak(self.curr_time, user)
                    pass
            self.compromised_users = list(set(self.compromised_users + self.curr_host.get_compromised_users()))
            if self.network.is_compromised(self.compromised_hosts):
                return
            # If target network, set adversary as done once adversary has compromised target node
            # if self.network.get_target_node() in self.compromised_hosts:
            #     if self.network.get_network_type() == 0:
            #         self.target_compromised = True
            #         return