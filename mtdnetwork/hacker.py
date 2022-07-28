import logging
from mtdnetwork.services import ServicesGenerator

import mtdnetwork.constants as constants
import mtdnetwork.exceptions as exceptions

class Hacker:

    def __init__(self, network):
        """
        Creates an instance of the Hacker that is trying to penetrate the network

        Parameters:
            network:
                the Network instance that this hacker is trying to compromise
        """
        self.network = network
        self.scorer = self.network.get_scorer()
        self.compromised_users = []
        self.compromised_hosts = []
        
        self.host_stack = []
        self.seen = []
        self.done = False

        self.action_manager = self.network.get_action_manager()
        self.action_manager.register_hacker(self)
        self.action = None

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
            "Total Host Compromises" : len(self.compromised_hosts),
            "Total User Compromises" : len(self.compromised_users),
            "Total Vuln Compromises" : self.total_vuln_compromise,
            "Total Reuse Pass Compromises" : self.total_reuse_pass_compromise,
            "Total Password Spray Compromises" : self.total_brute_force_compromise,
            "Total Actions Blocked by MTD" : self.total_blocked_by_mtd,
            "Compromised hosts" : self.compromised_hosts
        }

    def get_compromised(self):
        """
        Returns a list of compromised nodes
        """
        return self.compromised_hosts

    def log_host_result(self, reason):
        """
        Logs a result for a compromising a particular host

        Parameters:
            reason:
                the reason the host got compromised
        """
        self.logger.info("{}:{}:{}:{}".format(
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

    def handle_change(self, blocked_exceptions):
        """
        Responds to the changes that blocked the action and goes back to a previous
        action to remediate the issue.

        Parameters:
            blocked_exceptions:
                a list of exceptions that explain what was changed in the network that blocked the action
        """
        self.logger.info("MTD operation blocked action!")
        self.scorer.add_mtd_blocked_event(self.curr_time)
        self.total_blocked_by_mtd += 1

        # Temporarily add constants.HACKER_BLOCKED_BY_MTD_PENALITY to self.curr_time to add on the penality time for
        # being blocked by the MTD defense strategy which would waste time.
        time_penality = int(constants.HACKER_BLOCKED_BY_MTD_PENALITY*self.get_mtd_penality_discount(blocked_exceptions))
        self.logger.info("Time Penality: {}".format(time_penality))
        self.curr_time += time_penality

        if exceptions.HostIPChangeError in blocked_exceptions or \
            exceptions.PathToHostChangeError in blocked_exceptions:
            self.logger.info("Re-doing host discovery")
            self.start_network_enum()
            return
        
        if exceptions.PortsOnHostChangeError in blocked_exceptions or \
            exceptions.ServicesOnHostChangeError in blocked_exceptions or \
            exceptions.OSOnHostChangeError in blocked_exceptions:
            self.logger.info("Re-doing port scan on host {}".format(self.curr_host_id))
            self.start_port_scan()
            return

        if exceptions.UsersOnHostChangeError in blocked_exceptions:
            # If the hacker was just checking if a user has reused their password they should continue
            # to trying to discover vulnerabilities on the host.
            if self.action.complete_fn == self.check_reuse_user_pass:
                self.logger.info("Skipping checking if users have reused passwords!")
                self.find_vulns()
            else:
                self.logger.info("Giving up bruteforcing credentials on host {}! Moving to next target host!".format(self.curr_host_id))
                self.start_host_enum()
            return

    def step(self, curr_time):
        """
        Runs a step for the Hacker during the simulation

        Parameters:
            curr_time:
                the current time the simulation is at since the Hacker started attacking the network
        """
        self.curr_time = curr_time
        if self.done:
            return
        if self.action == None:
            self.start_network_enum()
        else:
            try:
                if self.action.check_if_completed(curr_time):
                    self.action.call_complete_fn()
            except exceptions.ActionBlockedError as e:
                self.handle_change(e.get_blocking_actions())

    def start_network_enum(self):
        """
        Starts the Network enumeration stage.
        """
        if not self.done:
            self.pivot_host_id = -1
            self.logger.info("SCANNING NETWORK FOR HOSTS")
            self.action = self.network.scan(self.compromised_hosts)
            self.action.set_trigger_time(self.curr_time)
            self.action.set_complete_fn(
                self.setup_host_enum
            )

    def setup_host_enum(self):
        """
        Sets up the order of hosts that the hacker will attempt to compromise

        The order is sorted by distance from the exposed endpoints which is done
        in the function self.network.scan().
        """
        self.host_stack = self.action.get_result()
        print("Setup host_enum run, host stack is: ", self.host_stack)
        self.start_host_enum()

    def start_scan_for_neighbors(self):
        """
        Starts scanning for neighbors from a host that the hacker can pivot to
        """
        self.action = self.curr_host.discover_neighbors()
        self.action.set_trigger_time(self.curr_time)
        self.action.set_complete_fn(
            self.setup_new_neighbors
        )

    def setup_new_neighbors(self):
        """
        Puts the new neighbors discovered to the start of the host stack.
        """
        found_neighbors = self.action.get_result()
        new_host_stack = found_neighbors + [
            node_id
                for node_id in self.host_stack
                    if not node_id in found_neighbors
        ]
        self.host_stack = new_host_stack
        self.start_host_enum()

    def start_host_enum(self):
        """
        Starts enumerating each host by popping off the host id from the top of the host stack

        TODO: Sort host_stack by distance from exposed endpoints AND previous compromised host
        """
        if len(self.host_stack) > 0:
            self.host_stack = self.network.sort_by_distance_from_exposed_and_pivot_host(
                self.host_stack, 
                self.compromised_hosts, 
                pivot_host_id=self.pivot_host_id
            )
            self.curr_host_id = self.host_stack.pop(0)
            self.curr_host = self.network.get_host(self.curr_host_id)
            self.curr_ports = []
            self.curr_vulns = []
            hop_time = int(constants.HACKER_HOP_TIME*self.network.get_shortest_distance_from_exposed_or_pivot(
                self.curr_host_id,
                pivot_host_id = self.pivot_host_id,
                graph = self.network.get_hacker_visible_graph()
            )) - 1
            if hop_time < 0:
                hop_time = 0
            # Add the time it takes to move a position to attack the target host
            self.curr_time += hop_time
            self.set_next_pivot_host()

            self.action = self.curr_host.is_compromised()
            self.action.set_trigger_time(self.curr_time)
            self.action.set_complete_fn(
                self.check_already_compromised
            )
        else:
            self.start_network_enum()

    def check_already_compromised(self):
        """
        Checks if the Hacker has already compromised and backdoored the target host

        NOTE: this function is deprecated but will be kept for now
        """
        already_compromised = self.action.get_result()
        self.debug_log("CHECK IF COMPROMISED")
        if already_compromised:
            self.debug_log("AUTO COMPROMISE")
            self.update_progress_state()
            self.pivot_host_id = self.curr_host_id
            self.start_host_enum()
        else:
            self.start_port_scan()

    def start_port_scan(self):
        """
        Starts a port scan on the target host
        """
        self.action = self.curr_host.port_scan()
        self.action.set_trigger_time(self.curr_time)
        self.action.set_complete_fn(
            self.process_port_scan
        )

    def process_port_scan(self):
        """
        Process the results from the port scan
        """
        self.curr_ports = self.action.get_result()
        self.debug_log("PROCESSED PORT SCAN")
        self.start_reuse_pass_check()

    def start_reuse_pass_check(self):
        """
        Checks if a compromised user has reused their credentials on the target host
        """
        self.action = self.curr_host.can_auto_compromise_with_users(
            self.compromised_users
        )
        self.action.set_trigger_time(self.curr_time)
        self.action.set_complete_fn(
            self.check_reuse_user_pass
        )

    def check_reuse_user_pass(self):
        """
        Gets the result that a user has reused their password on the target host.

        Otherwise it will go and try to exploit the vulnerabilities on the host
        """
        user_reuse = self.action.get_result()
        self.debug_log("CHECK FOR REUSED PASSWORDS")
        if user_reuse:
            self.log_host_result("USER REUSED PASS COMPROMISE")
            self.update_progress_state()
            self.pivot_host_id = self.curr_host_id
            self.total_reuse_pass_compromise += 1
            self.scorer.add_host_reuse_pass_compromise(self.curr_time, self.curr_host)
            self.start_scan_for_neighbors()
        else:
            self.find_vulns()

    def find_vulns(self):
        """
        Finds the top 5 vulnerabilities based on RoA score and have not been exploited yet that the
        """
        self.action = self.curr_host.get_vulns(self.curr_ports)
        self.action.set_trigger_time(self.curr_time)
        self.action.set_complete_fn(
            self.process_vulns
        )

    def process_vulns(self):
        """
        Processes the vulnerabilities that have been found
        """
        self.curr_vulns = self.action.get_result()
        self.debug_log("FOUND VULNS")
        self.exploit_host()

    def exploit_host(self):
        """
        Tries exploiting the vulnerabilities to compromise the host
        """
        self.action = self.curr_host.exploit_vulns(self.curr_vulns)
        self.action.set_trigger_time(self.curr_time)
        self.action.set_complete_fn(
            self.check_exploit_host
        )

    def check_exploit_host(self):
        """
        Checks if the adversary was able to successfully compromise the host
        """
        for vuln in self.curr_vulns:
            if vuln.is_exploited():
                self.scorer.add_vuln_compromise(self.curr_time, vuln)

        is_exploited = self.action.get_result()
        self.debug_log("ATTEMPT EXPLOIT VULNS")
        if is_exploited:
            self.log_host_result("VULN COMPROMISE")
            self.update_progress_state()
            self.pivot_host_id = self.curr_host_id
            self.total_vuln_compromise += 1
            self.scorer.add_host_vuln_compromise(self.curr_time, self.curr_host)
            self.start_scan_for_neighbors()
        else:
            self.brute_force_users()

    def brute_force_users(self):
        """
        Tries bruteforcing a login for a short period of time using previous passwords from compromised user accounts to guess a new login.
        """
        self.action = self.curr_host.compromise_with_users(
            self.compromised_users
        )
        self.action.set_trigger_time(self.curr_time)
        self.action.set_complete_fn(
            self.check_brute_force
        )

    def check_brute_force(self):
        """
        Checks if credentials for a user account has been successfully compromised.
        """
        brute_force_result = self.action.get_result()
        self.debug_log("ATTEMPT BRUTE FORCE USER")
        if brute_force_result:
            self.log_host_result("PASSWORD SPRAY USER COMPROMISE")
            self.update_progress_state()
            self.pivot_host_id = self.curr_host_id
            self.total_brute_force_compromise += 1
            self.scorer.add_host_pass_spray_compromise(self.curr_time, self.curr_host)
            self.start_scan_for_neighbors()
        else:
            self.start_host_enum()

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
        