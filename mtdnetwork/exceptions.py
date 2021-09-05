class PathToTargetNotFoundError(Exception):
    def __init__(self, target_node):
        self.message = "A path to {} could not be found!".format(target_node)
        super().__init__(self.message)

class NoHostProvidedError(Exception):
    def __init__(self):
        self.message = "You need to provide a host instance when doing an action on a host!"
        super().__init__(self.message)

class NoHostFoundError(Exception):
    def __init__(self):
        self.message = "No suitable host was found!"
        super().__init__(self.message)

class ActionBlockedError(Exception):
    def __init__(self, blocked_action_exceptions):
        """
        Raised when an action is blocked.

        Parameters:
            blocked_action_exceptions:
                the exceptions that were raised due to an aspect of the network being reconfigured so it would block the action
        """
        self.message = "The action has been blocked!"
        self.blocked_action_reasons = blocked_action_exceptions
        super().__init__(self.message)

    def get_blocking_actions(self):
        return self.blocked_action_reasons

class PortsOnHostChangeError(Exception):
    def __init__(self):
        self.message = "Ports on a host have changed!"
        super().__init__(self.message)

class HostIPChangeError(Exception):
    def __init__(self):
        self.message = "The IP address for a host has changed!"
        super().__init__(self.message)

class PathToHostChangeError(Exception):
    def __init__(self):
        self.message = "Path to host has changed!"
        super().__init__(self.message)

class ServicesOnHostChangeError(Exception):
    def __init__(self):
        self.message = "Services on a host have changed!"
        super().__init__(self.message)

class OSOnHostChangeError(Exception):
    def __init__(self):
        self.message = "The operating of a host have changed!"
        super().__init__(self.message)

class UsersOnHostChangeError(Exception):
    def __init__(self):
        self.message = "Users on a host have changed!"
        super().__init__(self.message)

class NetworkIPAddressesChangeError(Exception):
    def __init__(self):
        self.message = "IP addresses visible to the hacker have changed!"
        super().__init__(self.message)