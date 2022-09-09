import simpy

import mtdnetwork.constants as constants
from mtdnetwork.network.hacker import Hacker
import random
from scipy.stats import expon

HOST_SCAN = 0.01
HOST_ENUM = 0.01
CHECK_COMPROMISE = 0.01
CHECK_CREDENTIAL_REUSE = 0.01
SCAN_NEIGHBOUR = 0.01
PORT_SCAN = 10
EXPLOIT_VULNERABILITIES = 30
BRUTE_FORCE = 20


class Adversary(Hacker):
    def __init__(self, env, network, attack_threshold, attack_operation_record):
        super().__init__(network, attack_threshold)
        self.interrupted_by = None
        self.attack_operation_record = attack_operation_record
        self.env = env
        self.host_scan_process = env.process(self.host_scan_and_setup_host_enum(env, attack_operation_record))
        self.host_enum_process = None
        self.check_compromise_process = None
        self.check_credential_reuse_process = None
        self.scan_neighbour_process = None
        self.port_scan_process = None
        self.exploit_vulnerabilities_process = None
        self.brute_force_process = None

        # env.process(self.interrupt_attack())

    def host_scan_and_setup_host_enum(self, env, attack_operation_record):
        """
        Starts the Network enumeration stage.

        Sets up the order of hosts that the hacker will attempt to compromise

        The order is sorted by distance from the exposed endpoints which is done
        in the function adversary.network.host_scan().

        If the scan returns nothing from the scan, then the attacker will stop
        """
        self.pivot_host_id = -1
        self.host_stack = self.network.host_scan(self.compromised_hosts, self.stop_attack)
        yield env.timeout(HOST_SCAN)
        print("Processed host scan at %.1fs." % env.now)
        if len(self.host_stack) > 0:
            self.host_enum_process = env.process(self.start_host_enumeration(env, attack_operation_record))
        else:
            self.done = True

    def start_host_enumeration(self, env, attack_operation_record):
        """
        Starts enumerating each host by popping off the host id from the top of the host stack
        time for host hopping required
        """
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
            #     print("Current attack attempts: ", self.curr_attempts)

            self.curr_ports = []
            self.curr_vulns = []
            self.set_next_pivot_host()
            yield env.timeout(HOST_ENUM)
            self.check_compromise_process = env.process(self.check_host_already_compromised(env, attack_operation_record))
        else:
            self.host_scan_process = env.process(self.host_scan_and_setup_host_enum(env, attack_operation_record))

    def check_host_already_compromised(self, env, attack_operation_record):
        """
        Checks if the Hacker has already compromised and backdoored the target host
        """
        already_compromised = self.curr_host.is_compromised()
        yield env.timeout(CHECK_COMPROMISE)
        if already_compromised:
            # update_progress_state_info(self, env)
            # self.pivot_host_id = self.curr_host_id
            self.host_enum_process = env.process(self.start_host_enumeration(env, attack_operation_record))
        else:
            # Attack event triggered
            self.port_scan_process = env.process(self.start_and_process_port_scan(env, attack_operation_record))

    def start_and_process_port_scan(self, env, attack_operation_record):
        """
        Starts a port scan on the target host
        Phase 1
        """
        try:
            start_time = env.now
            self.curr_host.port_scan()
            yield env.timeout(PORT_SCAN)
            print("Processed port scan at %.1fs." % env.now)
            finish_time = env.now
            duration = env.now - start_time
            attack_operation_record.append({
                'name': 'PortScan',
                'start_time': start_time,
                'finish_time': finish_time,
                'duration': duration
            })
        except simpy.Interrupt:
            if self.interrupted_by == 'network':
                self.host_scan_process = env.process(self.host_scan_and_setup_host_enum)
            elif self.interrupted_by == 'application':
                 self.host_enum_process = env.process(self.start_host_enumeration(env, attack_operation_record))

        self.check_credential_reuse_process = env.process(self.start_credential_reuse_check(env, attack_operation_record))

    def start_credential_reuse_check(self, env, attack_operation_record):
        """
        Checks if a compromised user has reused their credentials on the target host
        """
        yield env.timeout(CHECK_CREDENTIAL_REUSE)
        print("Processed credential reuse check at %.1fs." % env.now)
        if self.curr_host.possible_user_compromise():
            c_reused_comp = True in [reused_pass for (username, reused_pass) in self.curr_host.users.items() if
                                     username
                                     in self.compromised_users]
            if c_reused_comp:
                self.log_host_result("USER REUSED PASS COMPROMISE")
                # update_progress_state_info(self, env)
                self.pivot_host_id = self.curr_host_id
                self.total_reuse_pass_compromise += 1
                # self.scorer.add_host_reuse_pass_compromise(self.curr_time, self.curr_host)
                self.scan_neighbour_process = env.process(self.scan_and_setup_new_neighbors(env, attack_operation_record))

        self.exploit_vulnerabilities_process = env.process(self.find_and_exploit_vulns(env, attack_operation_record))

    def find_and_exploit_vulns(self, env, attack_operation_record):
        """
        Finds the top 5 vulnerabilities based on RoA score and have not been exploited yet that the
        Tries exploiting the vulnerabilities to compromise the host
        Checks if the adversary was able to successfully compromise the host
        Phase 2
        """
        start_time = env.now
        services_dict = self.curr_host.get_services_from_ports(self.curr_ports, [])
        vulns = []
        discovery_time = 0
        for service_dict in services_dict:
            service = service_dict["service"]
            vulns = vulns + service.get_vulns(roa_threshold=0)
            discovery_time += service.discover_vuln_time(roa_threshold=0)
        new_vulns = []
        for vuln in vulns:
            if vuln.has_dependent_vulns:
                if vuln.can_exploit_with_dependent_vuln(vulns):
                    new_vulns.append(vuln)
            else:
                new_vulns.append(vuln)

        self.curr_vulns = new_vulns
        self.curr_attempts += len(self.curr_vulns)

        for vuln in self.curr_vulns:
            vuln.network(host=self.curr_host)
        services = self.curr_host.get_services(just_exploited=True)
        for service_id in services:
            if not service_id in self.curr_host.compromised_services:
                self.curr_host.compromised_services.append(service_id)
                self.curr_host.colour_map[service_id] = "red"
            if self.curr_host.target_node in list(self.curr_host.graph.neighbors(service_id)):
                self.curr_host.set_compromised()
        is_exploited = self.curr_host.compromised
        exploit_time = expon.rvs(scale=EXPLOIT_VULNERABILITIES, size=1)[0]
        yield env.timeout(exploit_time)
        print('Processed vulnerabilities exploitation at %.1fs' % env.now)
        finish_time = env.now
        duration = env.now - start_time
        attack_operation_record.append({
            'name': 'VulnerabilitiesExploit',
            'start_time': start_time,
            'finish_time': finish_time,
            'duration': duration
        })
        for vuln in self.curr_vulns:
            if vuln.is_exploited():
                # self.scorer.add_vuln_compromise(self.curr_time, vuln)
                pass
        if is_exploited:
            print('VULNERABILITY COMPROMISE AT %.1fs.' % env.now)
            # update_progress_state_info(self, env)
            self.pivot_host_id = self.curr_host_id
            self.total_vuln_compromise += 1
            # self.scorer.add_host_vuln_compromise(self.curr_time, self.curr_host)
            self.scan_neighbour_process = env.process(self.scan_and_setup_new_neighbors(env, attack_operation_record))
        else:
            self.brute_force_process = env.process(self.brute_force_users_login(env, attack_operation_record))

    def brute_force_users_login(self, env, attack_operation_record):
        """
        Tries bruteforcing a login for a short period of time using previous passwords from compromised user accounts to guess a new login.
        Checks if credentials for a user account has been successfully compromised.
        Phase 3
        """
        start_time = env.now
        self.curr_attempts += 1
        attempt_users = [username for username in self.curr_host.users.keys() if
                         username in self.compromised_users]
        yield env.timeout(BRUTE_FORCE)
        print('Processed brute force user at %.1fs.' % env.now)
        finish_time = env.now
        duration = env.now - start_time
        attack_operation_record.append({
            'name': 'BruteForce',
            'start_time': start_time,
            'finish_time': finish_time,
            'duration': duration
        })
        if random.random() < constants.HOST_MAX_PROB_FOR_USER_COMPROMISE * len(
                attempt_users) / self.curr_host.total_users:
            print('BRUTE FORCE SUCCESS AT %.1fs.' % env.now)
            self.curr_host.set_compromised()
            # update_progress_state_info(self, env)
            self.pivot_host_id = self.curr_host_id
            self.total_brute_force_compromise += 1
            # self.scorer.add_host_pass_spray_compromise(self.curr_time, self.curr_host)
            self.scan_neighbour_process = env.process(self.scan_and_setup_new_neighbors(env, attack_operation_record))
        else:
            self.host_enum_process = env.process(self.start_host_enumeration(env, attack_operation_record))

    def scan_and_setup_new_neighbors(self, env, attack_operation_record):
        """
        Starts scanning for neighbors from a host that the hacker can pivot to
        Puts the new neighbors discovered to the start of the host stack.
        """

        found_neighbors = list(self.curr_host.network.graph.neighbors(self.curr_host.host_id))
        new_host_stack = found_neighbors + [
            node_id
            for node_id in self.host_stack
            if not node_id in found_neighbors
        ]
        self.host_stack = new_host_stack
        yield env.timeout(SCAN_NEIGHBOUR)
        print('Processed scan neighbour at %.1f.' % env.now)
        self.host_enum_process = env.process(self.start_host_enumeration(env, attack_operation_record))

    # def interrupt_attack(self):
    #     while True:
    #         if self.done:
    #             self.process.interrupt()
    #
    # def update_progress_state_info(self, env):
    #     """
    #     Updates the Hackers progress state when it compromises a host.
    #     """
    #
    #     if not self.curr_host_id in self.compromised_hosts:
    #         self.compromised_hosts.append(self.curr_host_id)
    #         print("This host has been compromised at %.1f: " % env.now, self.curr_host_id)
    #         self.network.update_reachable_compromise(self.curr_host_id, self.compromised_hosts)
    #         for user in self.curr_host.get_compromised_users():
    #             if not user in self.compromised_users:
    #                 # self.scorer.add_user_account_leak(self.curr_time, user)
    #                 pass
    #         self.compromised_users = list(set(self.compromised_users + self.curr_host.get_compromised_users()))
    #         if self.network.is_compromised(self.compromised_hosts):
    #             return
    #         # If target network, set adversary as done once adversary has compromised target node
    #         if self.network.get_target_node() in self.compromised_hosts:
    #             if self.network.get_network_type() == 0:
    #                 self.target_compromised = True
    #                 return
