import mtdnetwork.constants as constants
import random
from scipy.stats import expon

HOST_SCAN = 0.1
HOST_ENUM = 0.1
CHECK_COMPROMISE = 0.1
CHECK_CREDENTIAL_REUSE = 0.1
SCAN_NEIGHBOUR = 0.1
PORT_SCAN = 2
EXPLOIT_TIME = 30
BRUTE_FORCE = 20


def host_scan_and_setup_host_enum(adversary, env, attack_operation_record):
    """
    Starts the Network enumeration stage.

    Sets up the order of hosts that the hacker will attempt to compromise

    The order is sorted by distance from the exposed endpoints which is done
    in the function adversary.network.host_scan().

    If the scan returns nothing from the scan, then the attacker will stop
    """
    adversary.pivot_host_id = -1
    adversary.host_stack = adversary.network.host_scan(adversary.compromised_hosts, adversary.stop_attack)
    yield env.timeout(HOST_SCAN)
    print("Processed host scan at %.1fs." % env.now)
    if len(adversary.host_stack) > 0:
        env.process(start_host_enumeration(adversary, env, attack_operation_record))
    else:
        return


def start_host_enumeration(adversary, env, attack_operation_record):
    """
    Starts enumerating each host by popping off the host id from the top of the host stack
    time for host hopping required
    """
    if len(adversary.host_stack) > 0:
        adversary.host_stack = adversary.network.sort_by_distance_from_exposed_and_pivot_host(
            adversary.host_stack,
            adversary.compromised_hosts,
            pivot_host_id=adversary.pivot_host_id
        )
        adversary.curr_host_id = adversary.host_stack.pop(0)
        adversary.curr_host = adversary.network.get_host(adversary.curr_host_id)
        # Sets node as unattackable if has been attack too many times
        adversary.attack_counter[adversary.curr_host_id] += 1
        if adversary.attack_counter[adversary.curr_host_id] == adversary.attack_threshold:
            # if adversary.curr_host_id != adversary.network.get_target_node():
            adversary.stop_attack.append(adversary.curr_host_id)

        # Checks if max attack attempts has been reached, empty stacks if reached
        if adversary.curr_attempts >= adversary.max_attack_attempts:
            adversary.host_stack = []
            return

        # Debugging attack attempts
        # if adversary.curr_attempts % 50 == 0:
        #     print("Current attack attempts: ", adversary.curr_attempts)

        adversary.curr_ports = []
        adversary.curr_vulns = []
        adversary.set_next_pivot_host()
        yield env.timeout(HOST_ENUM)
        env.process(check_host_already_compromised(adversary, env, attack_operation_record))
    else:
        env.process(host_scan_and_setup_host_enum(adversary, env, attack_operation_record))


def check_host_already_compromised(adversary, env, attack_operation_record):
    """
    Checks if the Hacker has already compromised and backdoored the target host
    """
    already_compromised = adversary.curr_host.is_compromised()
    yield env.timeout(CHECK_COMPROMISE)
    if already_compromised:
        # update_progress_state_info(adversary, env)
        # adversary.pivot_host_id = adversary.curr_host_id
        env.process(start_host_enumeration(adversary, env, attack_operation_record))
    else:
        # Attack event triggered
        env.process(start_and_process_port_scan(adversary, env, attack_operation_record))


def start_and_process_port_scan(adversary, env, attack_operation_record):
    """
    Starts a port scan on the target host
    Phase 1
    """
    start_time = env.now
    adversary.curr_host.port_scan()
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
    env.process(start_credential_reuse_check(adversary, env, attack_operation_record))


def start_credential_reuse_check(adversary, env, attack_operation_record):
    """
    Checks if a compromised user has reused their credentials on the target host
    """
    yield env.timeout(CHECK_CREDENTIAL_REUSE)
    print("Processed credential reuse check at %.1fs." % env.now)
    if adversary.curr_host.possible_user_compromise():
        c_reused_comp = True in [reused_pass for (username, reused_pass) in adversary.curr_host.users.items() if
                                 username
                                 in adversary.compromised_users]
        if c_reused_comp:
            adversary.log_host_result("USER REUSED PASS COMPROMISE")
            # update_progress_state_info(adversary, env)
            adversary.pivot_host_id = adversary.curr_host_id
            adversary.total_reuse_pass_compromise += 1
            # adversary.scorer.add_host_reuse_pass_compromise(adversary.curr_time, adversary.curr_host)
            env.process(scan_and_setup_new_neighbors(adversary, env, attack_operation_record))

    env.process(find_and_exploit_vulns(adversary, env, attack_operation_record))


def find_and_exploit_vulns(adversary, env, attack_operation_record):
    """
    Finds the top 5 vulnerabilities based on RoA score and have not been exploited yet that the
    Tries exploiting the vulnerabilities to compromise the host
    Checks if the adversary was able to successfully compromise the host
    Phase 2
    """
    start_time = env.now
    services_dict = adversary.curr_host.get_services_from_ports(adversary.curr_ports, [])
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

    adversary.curr_vulns = new_vulns
    adversary.curr_attempts += len(adversary.curr_vulns)

    for vuln in adversary.curr_vulns:
        vuln.exploit(host=adversary.curr_host)
    services = adversary.curr_host.get_services(just_exploited=True)
    for service_id in services:
        if not service_id in adversary.curr_host.compromised_services:
            adversary.curr_host.compromised_services.append(service_id)
            adversary.curr_host.colour_map[service_id] = "red"
        if adversary.curr_host.target_node in list(adversary.curr_host.graph.neighbors(service_id)):
            adversary.curr_host.set_compromised()
    is_exploited = adversary.curr_host.compromised
    exploit_time = expon.rvs(scale=EXPLOIT_TIME, size=1)[0]
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
    for vuln in adversary.curr_vulns:
        if vuln.is_exploited():
            # adversary.scorer.add_vuln_compromise(adversary.curr_time, vuln)
            pass
    if is_exploited:
        print('VULNERABILITY COMPROMISE AT %.1fs.' % env.now)
        # update_progress_state_info(adversary, env)
        adversary.pivot_host_id = adversary.curr_host_id
        adversary.total_vuln_compromise += 1
        # adversary.scorer.add_host_vuln_compromise(adversary.curr_time, adversary.curr_host)
        env.process(scan_and_setup_new_neighbors(adversary, env, attack_operation_record))
    else:
        env.process(brute_force_users_login(adversary, env, attack_operation_record))


def brute_force_users_login(adversary, env, attack_operation_record):
    """
    Tries bruteforcing a login for a short period of time using previous passwords from compromised user accounts to guess a new login.
    Checks if credentials for a user account has been successfully compromised.
    Phase 3
    """
    start_time = env.now
    adversary.curr_attempts += 1
    attempt_users = [username for username in adversary.curr_host.users.keys() if
                     username in adversary.compromised_users]
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
            attempt_users) / adversary.curr_host.total_users:
        print('BRUTE FORCE SUCCESS AT %.1fs.' % env.now)
        adversary.curr_host.set_compromised()
        # update_progress_state_info(adversary, env)
        adversary.pivot_host_id = adversary.curr_host_id
        adversary.total_brute_force_compromise += 1
        # adversary.scorer.add_host_pass_spray_compromise(adversary.curr_time, adversary.curr_host)
        env.process(scan_and_setup_new_neighbors(adversary, env, attack_operation_record))
    else:
        env.process(start_host_enumeration(adversary, env, attack_operation_record))


def scan_and_setup_new_neighbors(adversary, env, attack_operation_record):
    """
    Starts scanning for neighbors from a host that the hacker can pivot to
    Puts the new neighbors discovered to the start of the host stack.
    """

    found_neighbors = list(adversary.curr_host.network.graph.neighbors(adversary.curr_host.host_id))
    new_host_stack = found_neighbors + [
        node_id
        for node_id in adversary.host_stack
        if not node_id in found_neighbors
    ]
    adversary.host_stack = new_host_stack
    yield env.timeout(SCAN_NEIGHBOUR)
    print('Processed scan neighbour at %.1f.' % env.now)
    env.process(start_host_enumeration(adversary, env, attack_operation_record))


# def update_progress_state_info(adversary, env):
#     """
#     Updates the Hackers progress state when it compromises a host.
#     """
#
#     if not adversary.curr_host_id in adversary.compromised_hosts:
#         adversary.compromised_hosts.append(adversary.curr_host_id)
#         print("This host has been compromised at %.1f: " % env.now(, adversary.curr_host_id)
#         adversary.network.update_reachable_compromise(adversary.curr_host_id, adversary.compromised_hosts)
#         for user in adversary.curr_host.get_compromised_users():
#             if not user in adversary.compromised_users:
#                 # adversary.scorer.add_user_account_leak(adversary.curr_time, user)
#                 pass
#         adversary.compromised_users = list(
#             set(adversary.compromised_users + adversary.curr_host.get_compromised_users()))
#         if adversary.network.is_compromised(adversary.compromised_hosts):
#             return
#         # If target network, set adversary as done once adversary has compromised target node
#         if adversary.network.get_target_node() in adversary.compromised_hosts:
#             if adversary.network.get_network_type() == 0:
#                 adversary.target_compromised = True
#                 return
