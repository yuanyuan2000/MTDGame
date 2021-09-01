# Global constants for the simulation

OS_TYPES = [
    "windows",
    "ubuntu",
    "centos",
    "freebsd"
]

OS_VERSION_DICT = {
    "windows" : ["10", "8.1", "8", "7", "vista", "xp"],
    "ubuntu" : ["20.04", "18.04", "16.04", "14.04", "12.04", "10.04"],
    "centos" : ["8", "7", "6", "5", "4", "3"],
    "freebsd" : ["13", "12", "11", "10", "9", "8"]
}

SERVICE_VERSIONS = [x for x in range(1,100)]

LARGE_INT = (1 << 100000)

# No longer used and wordlists are included part of the package
# WORDLIST_URL = "https://www.mit.edu/~ecprice/wordlist.10000"
# NAME_LIST_URL = "https://raw.githubusercontent.com/dominictarr/random-name/master/first-names.txt"

# Constants for MTD strategies
MTD_MIN_TRIGGER_TIME = 100
MTD_MAX_TRIGGER_TIME = 2000

# Constants for Network
NETWORK_HOST_DISCOVER_TIME = 1

# Constants for Hosts
HOST_SERVICES_MIN = 1
HOST_SERVICES_MAX = 11
HOST_INTERNAL_SERVICE_MIN = 0
HOST_PORT_RANGE = range(1, 65546)
HOST_MAX_PROB_FOR_USER_COMPROMISE = 0.05
HOST_USER_COMPROMISE_TIME = 5
HOST_AUTO_COMPROMISE_TIME = 1
HOST_MAX_PROB_FOR_USER_COMPROMISE = 0.01
HOST_PORT_SCAN_MIN_TIME = 10
HOST_PORT_SCAN_MAX_TIME = 50

def nothing():
    """
    Does nothing
    """
    pass