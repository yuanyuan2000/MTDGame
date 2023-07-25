
import warnings
warnings.filterwarnings("ignore")
import matplotlib.pyplot as plt
plt.set_loglevel('WARNING')
import logging
logging.basicConfig(format='%(message)s', level=logging.INFO)

import simpy
import pandas as pd
from mtdnetwork.component.time_network import TimeNetwork
from mtdnetwork.operation.mtd_operation import MTDOperation
from mtdnetwork.data.constants import ATTACKER_THRESHOLD, OS_TYPES
from mtdnetwork.component.adversary import Adversary
from mtdnetwork.operation.attack_operation import AttackOperation
from mtdnetwork.snapshot.snapshot_checkpoint import SnapshotCheckpoint
from mtdnetwork.statistic.evaluation import Evaluation
from mtdnetwork.mtd.completetopologyshuffle import CompleteTopologyShuffle
from mtdnetwork.mtd.ipshuffle import IPShuffle
from mtdnetwork.mtd.hosttopologyshuffle import HostTopologyShuffle
from mtdnetwork.mtd.portshuffle import PortShuffle
from mtdnetwork.mtd.osdiversity import OSDiversity
from mtdnetwork.mtd.servicediversity import ServiceDiversity
from mtdnetwork.mtd.usershuffle import UserShuffle
from mtdnetwork.mtd.osdiversityassignment import OSDiversityAssignment
import random
import threading
import time
import queue

# Constants for game
WIDTH = 1000
HEIGHT = 500
NODE_RADIUS = 12
EDGE_WIDTH = 1

# def create_experiment_snapshots(network_size_list):
#     snapshot_checkpoint = SnapshotCheckpoint()
#     for size in network_size_list:
#         time_network = TimeNetwork(total_nodes=size)
#         adversary = Adversary(network=time_network, attack_threshold=ATTACKER_THRESHOLD)
#         snapshot_checkpoint.save_snapshots_by_network_size(time_network, adversary)

class Node:

    def __init__(self, num, x, y, color):
        self.id = num
        self.x = x
        self.y = y
        self.color = color

        self.is_chosen = False  # whether the node is chosen by users

class Game:
    def __init__(self) -> None:
        self.width = WIDTH
        self.height = HEIGHT

        self.isrunning = False
        self.room_id = None
        self.game_mode = None
        self.creator_role = None

        self.env = None
        self.sim_time = 0
        # self.snapshot_checkpoint = None
        self.time_network = None
        self.adversary = None
        self.attack_operation = None
        self.mtd_operation = None
        # self.evaluation = None
        self.nodes = []

    def get_isrunning(self):
        return self.isrunning
    
    def get_room_id(self):
        return self.room_id
    
    def get_creator_role(self):
        return self.creator_role
    
    def get_opponent_role(self):
        return self.opponent_role
    
    def get_game_mode(self):
        return self.game_mode
    
    def set_room_id(self, room_id):
        self.room_id = room_id

    def set_game_mode(self, game_mode):
        self.game_mode = game_mode

    def set_creator_role(self, creator_role):
        self.creator_role = creator_role

    def set_opponent_role(self, opponent_role):
        self.opponent_role = opponent_role

    def get_env(self):
        return self.env
    
    def get_snapshot_checkpoint(self):
        return self.snapshot_checkpoint
    
    def get_time_network(self):
        return self.time_network
    
    def get_adversary(self):
        return self.adversary
    
    def get_attack_operation(self):
        return self.attack_operation
    
    def get_mtd_operation(self):
        return self.mtd_operation
    
    def get_evaluation(self):
        return self.evaluation
    
    def get_nodes(self):
        return self.nodes
    
    def get_edges(self):
        edges = self.time_network.graph.edges
        # from pprint import pprint
        # def serialize_edges(edges):
        #     serialize_edges = []
        #     for edge in edges:
        #         serialize_edges.append(vars(edge))
        #     return serialize_edges
        # pprint(edges)
        return edges
    
    def get_haha(self):
        test_json = {
            'time_network.graph.nodes.get(host_id).os_type': self.time_network.graph.nodes[10]["host"].os_type,
            'time_network.graph.nodes.get(host_id).os_version': self.time_network.graph.nodes[10]["host"].os_version,
            'time_network.graph.nodes.get(host_id).host_id': self.time_network.graph.nodes[10]["host"].host_id,
            'time_network.graph.nodes.get(host_id).ip': self.time_network.graph.nodes[10]["host"].ip
        }
        return test_json
    
    def get_host_os_type(self, host_id):
        return self.time_network.graph.nodes[host_id]["host"].os_type
    
    def get_host_os_version(self, host_id):
        return self.time_network.graph.nodes[host_id]["host"].os_version
    
    def get_host_ip(self, host_id):
        return self.time_network.graph.nodes[host_id]["host"].ip
    
    def get_host_info(self, host_id):
        info = {
            'host_id': self.time_network.graph.nodes[host_id]["host"].host_id,
            'os_type': self.time_network.graph.nodes[host_id]["host"].os_type,
            'os_version': self.time_network.graph.nodes[host_id]["host"].os_version,
            'ip': self.time_network.graph.nodes[host_id]["host"].ip
        }
        return info

    def ip_shuffling(self, host_id):
        """
        Perform IP Shuffling MTD operation on the specified host.
        :param host_id: ID of the host that needs to perform IP shuffling operation.
        """
        # Get all hosts
        hosts = self.time_network.get_hosts()
        if host_id in hosts:
            # List to hold all IP addresses in the network
            existing_ips = [host.ip for host in hosts.values()]
            # Get the host that needs IP shuffling
            target_host = hosts[host_id]
            # Generate a new IP address that doesn't conflict with the existing ones
            new_ip = target_host.get_random_address(existing_addresses=existing_ips)
            # Assign the new IP to the host
            target_host.ip = new_ip
            print(f"IP address of host {host_id} has been changed to {new_ip}")
            return True
        else:
            print(f"Node {host_id} not found in the network.")
            return False
        
    def topology_shuffle(self):
        mtd_strategy = CompleteTopologyShuffle(network=self.time_network)
        mtd_strategy.mtd_operation()
        self.update_network()
        return True

    def os_diversity(self):
        mtd_strategy = OSDiversity(network=self.time_network)
        mtd_strategy.mtd_operation()
        return True

    def service_diversity(self, host_id):
        mtd_strategy = ServiceDiversity(network=self.time_network)
        mtd_strategy.mtd_operation(specific_host_id=host_id)
        return True

    def get_host_all_details(self, host_id):
        """
        This function get all details about a host by a given host_id.
        """
        all_details = None
        hosts = self.time_network.get_hosts()
        if host_id in hosts:
            # Get all services
            services_info = {}
            host = hosts[host_id]
            all_services = host.get_all_services()
            test_values = host.get_test_values()
            ports_dict, services_dict = test_values[0], test_values[1]

            for service in all_services:
                service_id = service.id
                service_name = service.name
                # Get the vulnerabilities of the service
                vulnerabilities = []
                for vulnerability in service.get_all_vulns():
                    vulnerabilities.append({
                        "Vulnerability ID": vulnerability.get_id(),
                        "Complexity": vulnerability.complexity,
                        "Impact": vulnerability.impact,
                        "CVSS": vulnerability.cvss,
                        "Exploitability": vulnerability.exploitability
                    })
                # Get the port of the service
                port = ports_dict.get(service_id)
                services_info[service_name] = {"vulnerabilities": vulnerabilities, "port": port, "service_id": service_id}

            # Return all details about this host
            all_details = {
                'host_id': self.time_network.graph.nodes[host_id]["host"].host_id,
                'os_type': self.time_network.graph.nodes[host_id]["host"].os_type,
                'os_version': self.time_network.graph.nodes[host_id]["host"].os_version,
                'ip': self.time_network.graph.nodes[host_id]["host"].ip,
                'is_compromised': host.is_compromised(),
                'service_info': services_info,
            }

            return all_details

    def print_all_service_info(self):
        service_generator = self.time_network.get_service_generator()
        for os_type, os_versions in service_generator.os_services.items():
            print(f'OS Type: {os_type}')
            for os_version, services in os_versions.items():
                print(f'  OS Version: {os_version}')
                for service_name, service_versions in services.items():
                    for service in service_versions:
                        print(f'    Service Name: {service.name}, Version: {service.version}')
                        for vulnerability in service.get_all_vulns():
                            print(f'      Vulnerability ID: {vulnerability.get_id()}, '
                                f'Complexity: {vulnerability.complexity}, '
                                f'Impact: {vulnerability.impact}, '
                                f'CVSS: {vulnerability.cvss}, '
                                f'Exploitability: {vulnerability.exploitability}')
                            
    def get_current_compromised_hosts(self):
        """
        return a list of host that has been compromised, such as [0, 11, 8, 9]
        """
        return self.adversary.get_compromised_hosts()
    
    def get_current_uncompromised_hosts(self):
        """
        return a list uncompromised host, such as [10, 21, 6, 1, 2, 3, 4]
        """
        compromised_hosts = self.get_current_compromised_hosts()
        uncompromised_hosts = []
        network = self.time_network
        visible_network = network.get_hacker_visible_graph()

        # Add every uncompromised host that is reachable and is not an exposed or compromised host
        for c_host in compromised_hosts:
            uncompromised_hosts = uncompromised_hosts + [
                neighbor
                for neighbor in network.graph.neighbors(c_host)
                if neighbor not in compromised_hosts and neighbor not in network.exposed_endpoints and
                len(network.get_path_from_exposed(neighbor, graph=visible_network)[0]) > 0
            ]

        # Add other uncompromised endpoints
        uncompromised_hosts = uncompromised_hosts + [
            ex_node
            for ex_node in network.exposed_endpoints
            if ex_node not in compromised_hosts
        ]

        return uncompromised_hosts
    
    def get_current_discovered_hosts(self):
        """
        discovered hosts is a list of hosts which is uncompromised and also not been label with 'stop attack', it can be used to continue attacking
        """
        uncompromised_hosts = self.get_current_uncompromised_hosts()
        stop_attack = self.adversary.get_stop_attack()
        discovered_hosts = [n for n in uncompromised_hosts if n not in stop_attack]
        return discovered_hosts
    
    def get_visible_hosts(self):
        return self.get_current_compromised_hosts() + self.get_current_uncompromised_hosts()
    
    def enum_host(self):
        adversary = self.adversary
        adversary.set_curr_process('ENUM_HOST')
        network = self.time_network
        adversary.set_host_stack(network.sort_by_distance_from_exposed_and_pivot_host(
                    adversary.get_host_stack(),
                    adversary.get_compromised_hosts(),
                    pivot_host_id=adversary.get_pivot_host_id()
                ))
        return adversary.get_host_stack()
    
    def scan_port(self, host_id):
        adversary = self.adversary
        adversary.set_curr_process('SCAN_PORT')
        network = self.time_network
        adversary.set_curr_host_id(host_id)
        adversary.set_curr_host(network.get_host(adversary.get_curr_host_id()))
        port_list = adversary.get_curr_host().port_scan()
        adversary.set_curr_ports(port_list)
        user_reuse = adversary.get_curr_host().can_auto_compromise_with_users(adversary.get_compromised_users())
        if user_reuse:
            # self.update_compromise_progress(self.env.now, self._proceed_time)
            # self._scan_neighbors()
            str = 'This node has been automatically compromised because of the same user password.'
        else:
            str = 'You can keep on attacking by clicking exploiting vulnerabilities button.'

        scan_port_result = {
                'port_list': port_list,
                'user_reuse': user_reuse,
                'message': str,
            }

        return scan_port_result
    
    def exploit_vuln(self, host_id):
        adversary = self.adversary
        adversary.set_curr_process('EXPLOIT_VULN')
        if host_id != adversary.get_curr_host_id():
            return -1
        else:
            adversary.set_curr_vulns(adversary.get_curr_host().get_vulns(adversary.get_curr_ports()))
            vulns = adversary.get_curr_vulns()

            def exponential_variates(loc, scale):
                from scipy.stats import expon
                return expon.rvs(loc=loc, scale=scale, size=1)[0]

            for vuln in vulns:
                exploit_time = exponential_variates(vuln.exploit_time(host=adversary.get_curr_host()), 0.5)
                start_time = self.env.now + self._proceed_time
                try:
                    logging.info(
                        "Adversary: Start %s %s on host %s at %.1fs." % (self.adversary.get_curr_process(), vuln.id,
                                                                         self.adversary.get_curr_host_id(), start_time))
                    yield self.env.timeout(exploit_time)
                except simpy.Interrupt:
                    self.env.process(self._handle_interrupt(start_time, self.adversary.get_curr_process()))
                    return
                finish_time = self.env.now + self._proceed_time
                logging.info(
                    "Adversary: Processed %s %s on host %s at %.1fs." % (self.adversary.get_curr_process(), vuln.id,
                                                                         self.adversary.get_curr_host_id(), finish_time))
                self.adversary.get_attack_stats().append_attack_operation_record(self.adversary.get_curr_process(),
                                                                                start_time,
                                                                                finish_time, self.adversary)
                vuln.network(host=adversary.get_curr_host())
                # cumulative vulnerability exploitation attempts
                adversary.set_curr_attempts(adversary.get_curr_attempts() + 1)

                if adversary.get_curr_host().check_compromised():
                    for vuln in adversary.get_curr_vulns():
                        if vuln.is_exploited():
                            if vuln.exploitability == vuln.cvss / 5.5:
                                vuln.exploitability = (1 - vuln.exploitability) / 2 + vuln.exploitability
                                if vuln.exploitability > 1:
                                    vuln.exploitability = 1
                                # todo: record vulnerability roa, impact, and complexity
                                # self.scorer.add_vuln_compromise(self.curr_time, vuln)
                    # self.update_compromise_progress(self.env.now, self._proceed_time)
                    # self._scan_neighbors()
                    return 0
                else:
                    return 1
                
    def brute_force(self, host_id):
        adversary = self.adversary
        if host_id != adversary.get_curr_host_id():
            return -1
        else:
            adversary.set_curr_process('BRUTE_FORCE')
            _brute_force_result = adversary.get_curr_host().compromise_with_users(
                adversary.get_compromised_users())
            if _brute_force_result:
                self.update_compromise_progress(self.env.now, self._proceed_time)
                self._scan_neighbors()
                return 1
            else:
                self._enum_host()
                return 0

    def _scan_neighbors(self):
        """
        Starts scanning for neighbors from a host that the hacker can pivot to
        Puts the new neighbors discovered to the start of the host stack.
        """
        adversary = self.adversary
        adversary.set_curr_process('SCAN_NEIGHBOR')
        found_neighbors = adversary.get_curr_host().discover_neighbors()
        new__host_stack = found_neighbors + [
            node_id
            for node_id in adversary.get_host_stack()
            if node_id not in found_neighbors
        ]
        adversary.set_host_stack(new__host_stack)

    def update_compromise_progress(self, now, proceed_time):
        """
        Updates the Hackers progress state when it compromises a host.
        """
        adversary = self.adversary
        adversary._pivot_host_id = adversary.get_curr_host_id()
        if adversary.get_curr_host_id() not in adversary.get_compromised_hosts():
            adversary.get_compromised_hosts().append(adversary.get_curr_host_id())
            adversary.get_attack_stats().update_compromise_host(adversary.curr_host)
            logging.info(
                "Adversary: Host %i has been compromised at %.1fs!" % (
                    adversary.get_curr_host_id(), now + proceed_time))
            adversary.get_network().update_reachable_compromise(
                adversary.get_curr_host_id(), adversary.get_compromised_hosts())

            for user in adversary.get_curr_host().get_compromised_users():
                if user not in adversary.get_compromised_users():
                    adversary.get_attack_stats().update_compromise_user(user)
            adversary._compromised_users = list(set(
                adversary.get_compromised_users() + adversary.get_curr_host().get_compromised_users()))
            if adversary.get_network().is_compromised(adversary.get_compromised_hosts()):
                # terminate the whole process
                self.end_event.succeed()
                return

    def update_network(self):
        """
        update the information about the network and the nodes in network
        """
        
        self.scale_x = 100
        self.scale_y = (self.height) // (self.time_network.max_y_pos - self.time_network.min_y_pos)
        self.shift_y = self.height - self.scale_y * self.time_network.max_y_pos

        pos_dict = self.time_network.pos
        color_list = self.time_network.colour_map
        self.nodes = []
        for key, color in zip(pos_dict, color_list):
            x = (pos_dict[key][0] * self.scale_x)
            y = (pos_dict[key][1] * self.scale_y) + self.shift_y
            self.nodes.append(Node(key, x, y, color))

    def start_real_time_simulation(self, period):
        # create a threading for real time simulation
        self.real_time_thread = threading.Thread(target=self._real_time_simulation, args=(period,))
        self.real_time_thread.start()

    def _real_time_simulation(self, period):
        start_time = time.perf_counter()   # the number of second from one fix moment
        while self.isrunning:
            time.sleep(period)
            last_time = self.sim_time
            self.sim_time = time.perf_counter() - start_time  # update the simulation time
            logging.info("Period from %.3f to %.3f" % (last_time, self.sim_time))
            # the game will end in 3000 simpy seconds
            if self.sim_time*300 < 3000:
                self.env.run(until=self.sim_time*300)
            else:
                break

    
    def execute_simulation(self, start_time=0, finish_time=None, scheme='random', mtd_interval=None, custom_strategies=None,
                        checkpoints=None, total_nodes=50, total_endpoints=5, total_subnets=8, total_layers=4,
                        target_layer=4, total_database=2, terminate_compromise_ratio=0.8, new_network=True):
        """
        :param start_time: the time to start the simulation, need to load timestamp-based snapshots if set start_time > 0
        :param finish_time: the time to finish the simulation. Set to None will run the simulation until
        the network reached compromised threshold (compromise ratio > 0.9)
        :param scheme: random, simultaneous, alternative, single, None
        :param mtd_interval: the time interval to trigger an MTD(s)
        :param custom_strategies: used for executing alternative scheme or single mtd strategy.
        :param checkpoints: a list of time value to save snapshots as the simulation runs.
        :param total_nodes: the number of nodes in the network (network size)
        :param total_endpoints: the number of exposed nodes
        :param total_subnets: the number of subnets (total_nodes - total_endpoints) / (total_subnets - 1) > 2
        :param total_layers: the number of layers in the network
        :param target_layer: the target layer in the network (for targetted attack scenario only)
        :param total_database: the number of database nodes used for computing DAP algorithm
        :param terminate_compromise_ratio: terminate the simulation if reached compromise ratio
        :param new_network: True: create new snapshots based on network size, False: load snapshots based on network size
        """
        self.env = simpy.Environment()
        end_event = self.env.event()
        # self.snapshot_checkpoint = SnapshotCheckpoint(env=self.env, checkpoints=checkpoints)
        

        # if start_time > 0:
        #     try:
        #         self.time_network, self.adversary = self.snapshot_checkpoint.load_snapshots_by_time(start_time)
        #     except FileNotFoundError:
        #         print('No timestamp-based snapshots available! Set start_time = 0 !')
        #         return
        # elif not new_network:
        #     try:
        #         self.time_network, self.adversary = self.snapshot_checkpoint.load_snapshots_by_network_size(total_nodes)
        #     except FileNotFoundError:
        #         print('set new_network=True')
        # else:
        self.time_network = TimeNetwork(total_nodes=total_nodes, total_endpoints=total_endpoints,
                                total_subnets=total_subnets, total_layers=total_layers,
                                target_layer=target_layer, total_database=total_database,
                                terminate_compromise_ratio=terminate_compromise_ratio)
        self.adversary = Adversary(network=self.time_network, attack_threshold=ATTACKER_THRESHOLD)
        # self.snapshot_checkpoint.save_snapshots_by_network_size(self.time_network, self.adversary)

        # update network information
        self.update_network()
        
        # from pprint import pprint
        # def serialize_nodes(nodes):
        #     serialized_nodes = []
        #     for node in nodes:
        #         serialized_nodes.append(vars(node))
        #     return serialized_nodes
        # pprint(serialize_nodes(self.nodes))


        # start attack
        self.attack_operation = AttackOperation(env=self.env, end_event=end_event, adversary=self.adversary, proceed_time=0)
        self.attack_operation.proceed_attack()

        # start mtd
        if scheme != 'None':
            self.mtd_operation = MTDOperation(env=self.env, end_event=end_event, network=self.time_network, scheme=scheme,
                                        attack_operation=self.attack_operation, proceed_time=0,
                                        mtd_trigger_interval=mtd_interval, custom_strategies=custom_strategies)
            self.mtd_operation.proceed_mtd()

        # save snapshot by time
        # if checkpoints is not None:
        #     self.snapshot_checkpoint.proceed_save(self.time_network, self.adversary)

        # start simulation
        if finish_time is not None:
            self.env.run(until=(finish_time - start_time))
        else:
            # self.env.run(until=end_event)
            self.start_real_time_simulation(0.5)


        # self.evaluation = Evaluation(network=self.time_network, adversary=self.adversary)


    def start(self):
        self.isrunning = True
        # create_experiment_snapshots([25, 50, 75, 100])
        self.execute_simulation(start_time=0, finish_time=None, mtd_interval=200, scheme='random', total_nodes=32, new_network=True)