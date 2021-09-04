import mtdnetwork.exceptions as exceptions
import mtdnetwork.constants as constants
import networkx as nx

class ActionCheck:

    def __init__(self, check_fn, fail_exception, check_args=[], check_kwargs={}):
        """
        Creates an Action Check that calls the check_fn function before an action starts and when
        it is supposed to be completed.

        An action is blocked if the check_fn returns a different result to the result when it was
        executed when the action is triggered.

        This is because if the result for the check_fn changes, it means that a MTD has reconfigured
        the network that thwarts the attacker from being capable of completing the action.

        Parameters:
            check_fn:
                the function to call for checking if the network has been changed
            check_args:
                a list of arguments for the check_fn
            check_kwargs:
                a dictionary of keyword arguments for the check_fn
            fail_exception:
                the exception to raise if the check discovers that there has been a change
        """
        self.check_fn = check_fn
        self.check_args = check_args
        self.check_kwargs = check_kwargs
        self.fail_exception = fail_exception
        self.initial_result = self.call_check_function()

    def call_check_function(self):
        """
        Calls the check function and returns the result of it.
        """
        return self.check_fn(self, *self.check_args, **self.check_kwargs)

    def check(self):
        """
        Checks if the network has changed that would block the action
        """
        result = self.call_check_function()

        if result != self.initial_result:
            raise self.fail_exception

class Action:

    def __init__(self, action_manager, result, time_to_complete, failed_fn, failed_fn_args, host_instance = None, check_ports = False, 
                    check_ip = False, check_path = False, check_services = False, check_os = False,
                    check_users = False, check_network_ips = False, check_network_paths = False):
        """
        Initialises an Action that checks if a change has occurred that would block the action.

        If the action is blocked then it will return the expected result. Otherwise it will signal that action has failed and the Hacker
        would have to remediate the issue.

        Parameters:
            action_manager:
                the ActionManager instance which is used to manage the actions of the simulation
            result:
                the result to return if the action successfully completed
            time_to_complete:
                the time it would take to complete the action
            failed_fn:
                the function to call if the action failed to revert the changes
            failed_fn_args:
                the arguments as a list for failed_fn
            host_instance:
                the Host instance to check for changes
            check_ports:
                checks if the ports on the host_instance have not changed
            check_ip:
                checks if the IP address of the host_instance has not chaned
            check_path:
                checks if the path to the host_instance has not chaned
            check_services:
                checks if the services on the host_instance have not changed
            check_os:
                checks if the OS and OS version have not changed on the host_instance
            check_users:
                checks if the users have not been changed on the host_instance
            check_network_ips:
                checks if the IP addresses on the hacker visible network have not changed
            check_network_paths:
                checks if the paths on the hacker visible network have not changed
                NOTE: uses a techinically incorrect implementation but it is good enough!
                      see the documentation for ActionManager().check_network_paths() for more information
        """
        if (check_ports or check_ip or check_path or check_services or check_os or check_users) and host_instance == None:
            raise exceptions.NoHostProvidedError

        self.action_manager = action_manager
        self.result = result
        self.time_to_complete = time_to_complete
        self.trigger_time = time_to_complete
        self.failed_fn = failed_fn
        self.failed_fn_args = failed_fn_args

        checks = []

        if check_ports:
            checks.append(ActionCheck(
                self.action_manager.check_ports_on_host,
                exceptions.PortsOnHostChangeError,
                check_args=[host_instance]
            ))
        
        if check_ip:
            checks.append(ActionCheck(
                self.action_manager.check_ip_for_host,
                exceptions.HostIPChangeError,
                check_args=[host_instance]
            ))

        if check_path:
            checks.append(ActionCheck(
                self.action_manager.check_path_to_host,
                exceptions.PathToHostChangeError,
                check_args=[host_instance]
            ))
        
        if check_services:
            checks.append(ActionCheck(
                self.action_manager.check_services_on_host,
                exceptions.ServicesOnHostChangeError,
                check_args=[host_instance]
            ))

        if check_os:
            checks.append(ActionCheck(
                self.action_manager.check_os_on_host,
                exceptions.OSOnHostChangeError,
                check_args=[host_instance]
            ))

        if check_users:
            checks.append(ActionCheck(
                self.action_manager.check_users_on_host,
                exceptions.UsersOnHostChangeError,
                check_args=[host_instance]
            ))

        if check_network_ips:
            checks.append(ActionCheck(
                self.action_manager.check_network_ip_addresses,
                exceptions.HostIPChangeError
            ))

        if check_network_paths:
            checks.append(ActionCheck(
                self.action_manager.check_network_paths,
                exceptions.PathToHostChangeError
            ))

        self.checks = checks

    def set_trigger_time(self, curr_time):
        """
        Sets the time when the completion of the Action will be triggered

        Parameters:
            curr_time:
                the current time the simulation is at
        """
        self.trigger_time += curr_time

    def get_completed_time(self):
        """
        Gets the time when the Action will be completed

        Returns:
            the time of when the Action will be completed
        """
        return self.trigger_time

    def get_result(self):
        """
        Returns the result of the Action

        Returns:
            whatever the result of the Action is.
            eg. IP addresses of hosts, open ports on a host, discovered services on a host, vulnerabilities of services, etc
        """
        return self.result

    def check_if_completed(self, curr_time):
        """
        Checks if the Action has completed, or something has blocked the action which raises an ActionBlockedError
        """
        failed = False
        failed_exceptions = []

        for actioncheck in self.checks:
            try:
                actioncheck.check()
            except Exception as e:
                failed_exceptions.append(e)
                failed = True

        if failed:
            self.failed_fn(*self.failed_fn_args)
            raise exceptions.ActionBlockedError(failed_exceptions)

        return curr_time >= self.get_completed_time()


class ActionManager:

    def __init__(self):
        self.network = None
        self.hacker = None

    def register_network(self, network):
        """
        Registers a network that it will monitor for changes when an action is occurring.

        Parameters:
            network:
                the network to monitor during the simulation
        """
        self.network = network
        network.register_action_manager(self)

    def register_hacker(self, hacker):
        """
        Registers a hacker that it will monitor for changes when an action is occurring.

        Parameters:
            hacker:
                the hacker to monitor
        """
        self.hacker = hacker
        hacker.register_action_manager(self)

    def check_ports_on_host(self, host_instance):
        """
        Returns the ports of the host_instance to see if they have been changed.

        Parameters:
            the Host instance to check if the ports have been changed
        """
        return host_instance.get_ports()

    def check_ip_for_host(self, host_instance):
        """
        Updates and returns the IP address for the Host instance for comparison.

        Parameters:
            the Host instance to check if the IP address has changed.
        """
        return host_instance.ip

    def check_path_to_host(self, host_instance):
        """
        Returns the shortest path to the target host using the compromised network.

        If a path change has occurred then that impacts the hacker then it will return a different path.

        Parameters:
            host_instance:
                the host to check if the path to it has been disrupted.
        """
        host_id = host_instance.host_id
        visible_network = self.network.get_hacker_visible_graph(self.hacker.compromised_hosts)
        try:
            return self.network.get_path_from_exposed(
                host_id,
                graph=visible_network
            )[0]
        except exceptions.PathToTargetNotFoundError:
            return []

    def check_services_on_host(self, host_instance):
        """
        Returns the services on a host to see if the services have been changed

        Parameters:
            host_instance:
                the host to check if the path to it has been disrupted.
        """
        return host_instance.get_services()

    def check_os_on_host(self, host_instance):
        """
        Checks if the OS and OS version are the same on the target machine.

        Parameters:
            host_instance:
                the host to check if the path to it has been disrupted.
        """
        return host_instance.get_os_type_and_version()

    def check_users_on_host(self, host_instance):
        """
        Checks if the same users are on the host.

        Parameters:
            host_instance:
                the host to check if the path to it has been disrupted.
        """
        return host_instance.get_users()

    def check_network_ip_addresses(self):
        """
        Checks if the IP addresses on a network that are visible to the hacker are the same.
        """
        visible_network = self.network.get_hacker_visible_graph(self.hacker.compromised_hosts)

        ip_addresses = [
            self.network.get_host(visible_node_id).get_ip()
                for visible_node_id in visible_network.nodes
        ]

        return sorted(ip_addresses)

    def check_network_paths(self):
        """
        Checks if the paths on the hacker visible network are the same.

        NOTE
        This method is a bit of a hacky solution and isn't technically correct since it is
        just testing ismorphism and not actually if paths are the same. It is close enough though
        for this simulation but do consider changing this implementation
        """
        visible_network = self.network.get_hacker_visible_graph(self.hacker.compromised_hosts)
        return nx.weisfeiler_lehman_graph_hash(visible_network)

    def create_action(self, result, time_to_complete, failed_fn=constants.nothing, failed_fn_args=[], host_instance = None, check_ports = False, 
                        check_ip = False, check_path = False, check_services = False, check_os = False,
                        check_users = False, check_network_ips = False, check_network_paths = False):
        """
        Creates an Action that can be blocked by a network reconfiguration.

        Parameters:
            result:
                the result to return if the action successfully completed
            time_to_complete:
                the time it would take to complete the action
            failed_fn:
                the function to call if the action has failed to revert the changes that would of been caused by the action
            failed_fn_args:
                the args for the failed_fn
            host_instance:
                the Host instance to check for changes
            check_ports:
                checks if the ports on the host_instance have not changed
            check_ip:
                checks if the IP address of the host_instance has not chaned
            check_path:
                checks if the path to the host_instance has not chaned
            check_services:
                checks if the services on the host_instance have not changed
            check_os:
                checks if the OS and OS version have not changed on the host_instance
            check_users:
                checks if the users have not been changed on the host_instance
            check_network_ips:
                checks if the IP addresses on the hacker visible network have not changed
            check_network_paths:
                checks if the paths on the hacker visible network have not changed
                NOTE: uses a techinically incorrect implementation but it is good enough!
                      see the documentation for ActionManager().check_network_paths() for more information

        Returns:
            an Action instance which the hacker will use to check if the Action has completed or
            it has been blocked.
        """
        
        return Action(self, result, time_to_complete, host_instance, failed_fn, failed_fn_args, check_ports = check_ports, 
                        check_ip = check_ip, check_path = check_path, check_services = check_services,
                        check_os = check_os, check_users = check_users, check_network_ips = check_network_ips,
                        check_network_paths = check_network_paths)

        