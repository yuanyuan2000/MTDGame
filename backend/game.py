
import warnings
warnings.filterwarnings("ignore")
import matplotlib.pyplot as plt
plt.set_loglevel('WARNING')
import logging
logging.basicConfig(format='%(message)s', level=logging.INFO)

import simpy
import pandas as pd
import networkx as nx
from mtdnetwork.component.time_network import TimeNetwork
from mtdnetwork.operation.mtd_operation import MTDOperation
from mtdnetwork.data.constants import ATTACKER_THRESHOLD, OS_TYPES, NODE_COLOURS
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
from collections import deque

# Constants for game
WIDTH = 1000
HEIGHT = 500
NODE_RADIUS = 12
EDGE_WIDTH = 1

SIMULATION_INTERVAL = 0.5    # the simpy will run in every SIMULATION_INTERVAL second
GAME_TOTAL_TIME = 300    # the game will end in GAME_TOTAL_TIME simulation seconds
SPEED_RATIO = 10    # it means that one physcial second equal to SPEED_RATIO simulation seconds

TOTAL_NODE = 32
TOTAL_TARGET_NODE_NUM = 3

EXPLOIT_VULN_DURATION = 3   # physical second
BRUTE_FORCE_DURATION = 5   # physical second
MAX_TOPO_SHUFFLE_TIME = 2
OS_RECOVERY = 0.15       # the probability to recover a node when OS diversity in human vs computer mode
SERVICE_RECOVERY = 0.3    # the probability to recover a node when service diversity in human vs computer mode

class Node:

    def __init__(self, num, x, y, color):
        self.id = num
        self.x = x
        self.y = y
        self.color = color

class Game:
    def __init__(self) -> None:
        self.width = WIDTH
        self.height = HEIGHT

        self.isrunning = False
        self.room_id = None
        self.game_mode = None
        self.creator_role = None
        self.winner = None

        self.env = None
        self.sim_time = 0
        self.total_time = GAME_TOTAL_TIME / SPEED_RATIO
        self.finished_event = None

        self.time_network = None
        self.adversary = None
        self.attack_operation = None
        self.mtd_operation = None

        self.nodes = []
        self.target_node_num_list = []
        self.attacker_visible_nodes = []
        self.attacker_visible_edges = []
        self.scan_port_progress = []   # a bool list(len:TOTAL_NODE), False means this node has not been scaned port(will be reset by OS/service diversity)
        self.exploit_vuln_progress = []  # a bool list(len:TOTAL_NODE), True means this node has been compromised because of an exploited service(not brute force)
        self.brute_force_progress = []  # a bool list(len:TOTAL_NODE), False means the progress has been interrupt by user MTD operation
        self.attacker_new_message = deque()   # a queue that store new messages for sending to the attacker, it will be deleted after sending
        self.attacker_message_id_counter = 0
        self.topo_shuffle_time = 0
        self.compromised_services = []   # a list to store all the compromised service name
        
    def get_isrunning(self):
        return self.isrunning
    
    def get_room_id(self):
        return self.room_id
    
    def get_creator_role(self):
        return self.creator_role
    
    def get_game_mode(self):
        return self.game_mode
    
    def get_winner(self):
        return self.winner
    
    def get_sim_time(self):
        return self.sim_time
    
    def get_total_time(self):
        return self.total_time
    
    def set_room_id(self, room_id):
        self.room_id = room_id

    def set_game_mode(self, game_mode):
        self.game_mode = game_mode

    def set_creator_role(self, creator_role):
        self.creator_role = creator_role

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
        self.update_network()
        return self.nodes
    
    def get_edges(self):
        edges = self.time_network.graph.edges
        return edges

    def get_attacker_new_message(self):
        messages = list(self.attacker_new_message)[-10:]   # only send the 10 newest messagess
        # for message in messages:
        #     logging.info(f"Sent message to frontend: {message}")
        return messages
    
    def add_attacker_new_message(self, message_content):
        message_id = self.attacker_message_id_counter
        self.attacker_new_message.append({'id': message_id, 'content': message_content})
        self.attacker_message_id_counter += 1

        # if the number of messages more than 10, delete the old messages
        if len(self.attacker_new_message) > 10:
            self.attacker_new_message.popleft()
    
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
        hosts = self.time_network.get_hosts()
        if host_id in hosts:
            existing_ips = [host.ip for host in hosts.values()]  # list to hold all IP addresses in the network
            target_host = hosts[host_id]
            # Generate a new IP address that doesn't conflict with the existing ones
            new_ip = target_host.get_random_address(existing_addresses=existing_ips)
            target_host.ip = new_ip
            # Interrupt the brute force progress for this IP
            self.brute_force_progress[host_id] = False
            self._interrupt_adversary(mtd_type=0)
            return True
        else:
            return False
        
    def topology_shuffle(self):
        if self.topo_shuffle_time < MAX_TOPO_SHUFFLE_TIME:
            mtd_strategy = CompleteTopologyShuffle(network=self.time_network)
            mtd_strategy.mtd_operation()
            self._interrupt_adversary(mtd_type=1)
            self.update_network()
            self.topo_shuffle_time += 1
            self.set_visible_hosts()
            self.set_visible_edges()
            self.add_attacker_new_message(f"Message: It seems defender have changed the topology of network")
            self.add_attacker_new_message(f"Try rescan host please")
            return 1
        else:
            return 0

    def os_diversity(self):
        someone_recovery, recovery_list, msg = False, [], f'You have finished the OS diversity for all nodes. Now they are more difficult for attacker to exploit vulnerabilities.'
        mtd_strategy = OSDiversity(network=self.time_network)
        mtd_strategy.mtd_operation()
        self.scan_port_progress = [False for _ in range(TOTAL_NODE)]

        for index in range(TOTAL_NODE):
            recovery_result = False
            # when human vs human, get recovery result by judging if the node is still exploited when the node is compromised because of exploit
            if self.get_game_mode() == 'Human' and self.exploit_vuln_progress[index]:
                recovery_result = not self.judge_if_still_exploited(index)
            # when human vs computer, get recovery result by probability when the node is compromised
            if self.get_game_mode() == 'Computer' and index in self.get_current_compromised_hosts():
                recovery_result = random.random() < OS_RECOVERY
            if recovery_result:
                self.recovery_a_node(index)
                self.exploit_vuln_progress[index] = False
                someone_recovery = True
                recovery_list.append(index)

        self._interrupt_adversary(mtd_type=2)

        if someone_recovery:
            msg = f'The node {", ".join(map(str, recovery_list))} have been set to uncompromised because you change some services on them.'

        return {'message': msg, }

    def service_diversity(self, host_id):
        if host_id in self.time_network.exposed_endpoints:
            msg = f'You can not change the services on an endpoint(green node). Because it need to keep running for your users.'
        else:
            if host_id in self.get_current_compromised_hosts():
                msg = f'You have changed some services on node {host_id} but it is still compromised. There are 2 reasons: 1. Compromised is not because some services on OS is exploited. 2. Some exploited services are still running on it.'
            else:
                msg = f'You have changed some services on node {host_id}.'
            mtd_strategy = ServiceDiversity(network=self.time_network)
            mtd_strategy.mtd_operation(specific_host_id=host_id)
            self.scan_port_progress[host_id] = False

            recovery_result = False
            if self.get_game_mode() == 'Human' and self.exploit_vuln_progress[host_id]:
                recovery_result = not self.judge_if_still_exploited(host_id)
            if self.get_game_mode() == 'Computer' and host_id in self.get_current_compromised_hosts():
                recovery_result = random.random() < SERVICE_RECOVERY
            if recovery_result:
                self.recovery_a_node(host_id)
                self.exploit_vuln_progress[host_id] = False
                msg = f'The node {host_id} has been set to uncompromised because you change some services on it.'

            self._interrupt_adversary(mtd_type=3)
        
        return {'message': msg, }
    
    def judge_if_still_exploited(self, host_id):
        """
        judge if a node is still exploited after diversity
        """
        hosts = self.time_network.get_hosts()
        if host_id in hosts:
            host = hosts[host_id]
            all_services = host.get_all_services()
            for service in all_services:
                service_name = service.name
                if service_name in self.compromised_services:
                    return True
        return False
    
    def _interrupt_adversary(self, mtd_type):
        """
        interrupt the attack process of the adversary, only used when the computer is attacker
        mtd_type: IP shuffling, topological shuffling, OS diversity, service diversity -> 0, 1, 2, 3
        """
        return   # there is still some bugs in this part will terminate the whole simulation when we interrupt
        if self.get_game_mode() == 'Computer' and self.get_creator_role() == 'defender':
            attack_process = self.attack_operation.get_attack_process()
            if attack_process is not None and attack_process.is_alive:
                logging.info('MTD: Interrupted %s at %.1fs!' % (self.attack_operation.get_adversary().get_curr_process(), self.env.now))
                if mtd_type == 0 or mtd_type == 1:
                    self._interrupted_mtd = None
                    self.adversary.set_curr_host_id(-1)
                    self.adversary.set_curr_host(None)
                    logging.info('Adversary: Restarting with SCAN_HOST at %.1fs!' % (self.env.now))
                    self.attack_operation._scan_host()
                elif mtd_type == 2 or mtd_type == 3:
                    self._interrupted_mtd = None
                    logging.info('Adversary: Restarting with SCAN_PORT at %.1fs!' % (self.env.now))
                    self.attack_operation._scan_port()
                
                self.time_network.get_mtd_stats().add_total_attack_interrupted()

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
        return a list of host that has been compromised, such as [0, 1, 2]
        """
        compromised_hosts = self.adversary.get_compromised_hosts()
        return sorted(set(compromised_hosts))
    
    # this function is not used now, can be commented
    def get_current_uncompromised_hosts(self):
        """
        return a list uncompromised host, such as [5, 7, 8], which are the set of neighbours of compromised hosts and the endpoints
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

        return sorted(set(uncompromised_hosts))
    
    def get_visible_hosts(self):
        """
        when the attacker use this API to get the visble data to do some operation or draw the network
        we need to judge if the nodes are still in the can_visible_list(the compromised and uncompromised hosts)
        because some nodes may become unvisible because of some MTD operation during this time
        """
        # can_visible_list = self.get_current_compromised_hosts() + self.get_current_uncompromised_hosts()
        # self.attacker_visible_nodes = [node for node in self.attacker_visible_nodes if node in can_visible_list]
        return self.attacker_visible_nodes
    
    def get_visible_edges(self):
        return [index + 1 for index, is_visible in enumerate(self.attacker_visible_edges) if is_visible]
    
    def set_visible_hosts(self):
        """
        this function is used to reset the value of the self.attacker_visible_nodes after some MTD opertion or when the game starts
        only the exposed endpoints and the compromised host can be set as visible
        """
        exposed_endpoints = self.time_network.exposed_endpoints
        compromised_hosts = self.get_current_compromised_hosts()
        can_visible_list = set(exposed_endpoints + compromised_hosts)
        self.attacker_visible_nodes = [i for i in can_visible_list]

    def set_visible_edges(self):
        """
        set all the edges visibility to False
        """
        self.attacker_visible_edges = [False] * len(self.get_edges())

    def judge_if_reachable(self, host_id):
        """
        judge if it is reachable from the endpoints to the host_id node
        we can simply judge by checking if all edges connected to the host_id are invisible, if so, there is no visible path from the endpoints to this node
        """
        def transform_edges(edges):
            transformed_edges = []
            for idx, edge in enumerate(edges, start=1):
                transformed_edges.append({ "id": idx, "from": edge[0], "to": edge[1] })
            return transformed_edges
        edges = transform_edges(self.get_edges())
        exposed_endpoints = self.time_network.exposed_endpoints
        if host_id not in exposed_endpoints:
            all_edges_invisible = True
            for edge in edges:
                if (edge['from'] == host_id or edge['to'] == host_id) and self.attacker_visible_edges[edge['id'] - 1]:
                    all_edges_invisible = False
                    break

            if all_edges_invisible:
                return False
        return True

    def scan_host(self, host_id):
        """
        update the attacker visible nodes, so next interval when the get_visible_hosts() is used the attacker will see more nodes
        return 0 if the host_id is uncompromised, because only the compromised hosts can scan their neighbour
        return -1 if this node is not reachable
        """
        if host_id not in self.get_current_compromised_hosts():
            return 0
        
        if not self.judge_if_reachable(host_id):
            return -1
        
        def transform_edges(edges):
            transformed_edges = []
            for idx, edge in enumerate(edges, start=1):
                transformed_edges.append({ "id": idx, "from": edge[0], "to": edge[1] })
            return transformed_edges
        edges = transform_edges(self.get_edges())
        
        # Find all the nodes connected with the host_id and set them and their edge to be visible
        for edge in edges:
            if edge['from'] == host_id or edge['to'] == host_id:
                connected_node_id = edge['to'] if edge['from'] == host_id else edge['from']
                self.attacker_visible_nodes.append(connected_node_id)
                self.attacker_visible_edges[edge['id'] - 1] = True
                # logging.info(f"set the edge connect from {edge['from']} to {edge['to']} to be True")

        return 1

    def scan_port(self, host_id):
        """
        Starts a port scan on the target host
        Checks if a compromised user has reused their credentials on the target host
        Phase 1
        """
        host_id_str = str(host_id)
        hosts = self.get_visible_hosts()
        adversary = self.adversary
        
        port_list, user_reuse, msg = None, -1, f'The node {host_id_str} is illegal to scan the port because it is unvisble or unreachable to the attacker.'
        if host_id in hosts and self.judge_if_reachable(host_id):
            adversary.set_curr_host_id(host_id)
            adversary.set_curr_host(self.time_network.get_host(adversary.get_curr_host_id()))
            adversary.set_curr_ports([])
            adversary.set_curr_vulns([])           
            adversary.get_attack_counter()[adversary.get_curr_host_id()] += 1
            adversary.get_attack_stats().append_attack_operation_record('SCAN_PORT', self.env.now, self.env.now, adversary)

            port_list = adversary.get_curr_host().port_scan()
            adversary.set_curr_ports(port_list)
            self.scan_port_progress[host_id] = True
            # for game balance, p(reuse password) = 0+num_compromised_hosts/(2*TOTAL_NODE), so it is [0, 0.5] (depends on the numer of compromised hosts)
            def probability_function():
                num_compromised_hosts = len(self.get_current_compromised_hosts())
                x = 0 + num_compromised_hosts / (2 * TOTAL_NODE)
                random_number = random.random()
                return random_number < x
            # user_reuse = adversary.get_curr_host().can_auto_compromise_with_users(adversary.get_compromised_users())
            user_reuse = probability_function()
            msg = f'The node {host_id_str} has been automatically compromised because of the same user password.' if user_reuse else f'You can keep on attacking node {host_id_str} by exploiting vulnerabilities according to the port list: {", ".join(map(str, port_list))}'
            if user_reuse:
                self.__update_compromise_progress()
                self.__scan_neighbors()
                self.time_network.colour_map[adversary.get_curr_host_id()] = "red"

        self.update_network()
        return {'port_list': port_list, 'user_reuse': user_reuse, 'message': msg, }
    
    def start_exploit_vuln(self, host_id):
        # return 1 if the host has been compromised
        if host_id in self.get_current_compromised_hosts():
            return 1
        # return -1 if the host is unvisible(it will happen when some MTD executed after attacker choose a node and before him click the button)
        # or because it is not reachable now(it will happen after a topological shuffling and no visible path from endpoints to this node)
        elif host_id not in self.get_visible_hosts() or self.judge_if_reachable(host_id) is not True:
            return -1
        # return -2 if no port has been scaned for this node
        elif self.scan_port_progress[host_id] is not True:
            return -2
        # return 0 before running finish_exploit_vuln in EXPLOIT_VULN_DURATION seconds, this node should be visible and reachable
        else:
            timer = threading.Timer(EXPLOIT_VULN_DURATION, self.finish_exploit_vuln, args=(host_id,))
            timer.start()
            return 0
    
    def finish_exploit_vuln(self, host_id):
        adversary = self.adversary
        adversary.set_curr_host_id(host_id)
        adversary.set_curr_host(self.time_network.get_host(adversary.get_curr_host_id()))
        adversary.set_curr_ports([])
        adversary.set_curr_vulns([])           
        adversary.get_attack_counter()[adversary.get_curr_host_id()] += 1
        adversary.set_curr_ports(adversary.get_curr_host().port_scan())
        adversary.set_curr_vulns(adversary.get_curr_host().get_vulns(adversary.get_curr_ports()))
        adversary.get_attack_stats().append_attack_operation_record('EXPLOIT_VULN', self.env.now - SPEED_RATIO * EXPLOIT_VULN_DURATION, self.env.now, adversary)
        
        vulns = adversary.get_curr_vulns()
        for vuln in vulns:
            # logging.info("Adversary: Processed %s %s on host %s at %.1fs." % (adversary.get_curr_process(), vuln.id,
            #                                                          adversary.get_curr_host_id(), self.env.now))
            vuln.network(host=adversary.get_curr_host())
            adversary.set_curr_attempts(adversary.get_curr_attempts() + 1)
            
        exploit_result = adversary.get_curr_host().check_compromised()

        if host_id in self.get_current_compromised_hosts():
            self.add_attacker_new_message(f"Message: Node {host_id} has been already compromised")
        elif self.scan_port_progress[host_id] is not True:
            self.add_attacker_new_message(f"Message: Exploiting vulnerability of services on node {host_id} failed")
            self.add_attacker_new_message(f"It may because some MTD operation changed the port number.")
        else:
            if exploit_result:
                # get the exploited services
                exploited_services = adversary.get_curr_host().get_services(just_exploited=True)
                service_names = [service.name for service in exploited_services.values()]

                # add the new exploited service name to the compromised_services list
                compromised_services_set = set(self.compromised_services)
                compromised_services_set.update(service_names)
                self.compromised_services = list(compromised_services_set)

                for vuln in adversary.get_curr_vulns():
                    if vuln.is_exploited():
                        if vuln.exploitability == vuln.cvss / 5.5:
                            vuln.exploitability = (1 - vuln.exploitability) / 2 + vuln.exploitability
                            if vuln.exploitability > 1:
                                vuln.exploitability = 1

                self.__update_compromise_progress()
                self.__scan_neighbors()
                self.time_network.colour_map[adversary.get_curr_host_id()] = "red"
                self.exploit_vuln_progress[host_id] = True
                self.add_attacker_new_message(f"Message: Node {host_id} vulnerability exploited")
                self.add_attacker_new_message(f'Current exploited services: {", ".join(map(str, self.compromised_services))}')
            else:
                self.add_attacker_new_message(f"Message: Exploiting vulnerability of services on node {host_id} failed")
                self.add_attacker_new_message(f"It may because few services on this host are vulnerable.")
            
        self.update_network()
        
    def start_brute_force(self, host_id):
        if host_id in self.get_current_compromised_hosts():
            return 1
        elif host_id in self.get_visible_hosts() and self.judge_if_reachable(host_id):
            # set the brute force progress to be True before attacking
            self.brute_force_progress[host_id] = True
            # create a Timer to run finish_brute_force in BRUTE_FORCE_DURATION seconds
            timer = threading.Timer(BRUTE_FORCE_DURATION, self.finish_brute_force, args=(host_id,))
            timer.start()
            return 0
        else:
            return -1
                
    def finish_brute_force(self, host_id):
        adversary = self.adversary
        adversary.set_curr_host_id(host_id)
        adversary.set_curr_host(self.time_network.get_host(adversary.get_curr_host_id()))
        adversary.set_curr_ports([])
        adversary.set_curr_vulns([])           
        adversary.get_attack_counter()[adversary.get_curr_host_id()] += 1
        adversary.get_attack_stats().append_attack_operation_record('BRUTE_FORCE', self.env.now - SPEED_RATIO * BRUTE_FORCE_DURATION, self.env.now, adversary)

        # for game balance, p(brute force) = 0.4+num_compromised_hosts/(2*TOTAL_NODE), so it is [0.4, 0.9] (depends on the numer of compromised hosts)
        def probability_function():
            num_compromised_hosts = len(self.get_current_compromised_hosts())
            x = 0.4 + num_compromised_hosts / (2 * TOTAL_NODE)
            random_number = random.random()
            return random_number < x
        # brute_force_result = adversary.get_curr_host().compromise_with_users(adversary.get_compromised_users())
        brute_force_result = probability_function()

        if host_id in self.get_current_compromised_hosts():
            self.add_attacker_new_message(f"Message: Node {host_id} has been already compromised")
        else:
            if brute_force_result and self.brute_force_progress[host_id]:
                self.__update_compromise_progress()
                self.__scan_neighbors()
                self.time_network.colour_map[host_id] = "red"
                self.add_attacker_new_message(f"Message: Node {host_id} was brute-forced")
            elif self.brute_force_progress[host_id]:
                self.add_attacker_new_message(f"Message: Brute-forcing node {host_id} failed")
                self.add_attacker_new_message(f"It may because you haven't get enough proper passwords.")
            else:
                self.add_attacker_new_message(f"Message: Brute-forcing node {host_id} failed")
                self.add_attacker_new_message(f"It may because some MTD operation interrupt your progress.")
        
        self.update_network()

    def __scan_neighbors(self):
        """
        Starts scanning for neighbors from a host that the hacker can pivot to
        Puts the new neighbors discovered to the start of the host stack.
        """
        adversary = self.adversary
        found_neighbors = adversary.get_curr_host().discover_neighbors()
        new__host_stack = found_neighbors + [
            node_id
            for node_id in adversary.get_host_stack()
            if node_id not in found_neighbors
        ]
        adversary.set_host_stack(new__host_stack)

    def __update_compromise_progress(self):
        """
        Updates some parameters when the current host is compromised
        """
        adversary = self.adversary
        adversary._pivot_host_id = adversary.get_curr_host_id()
        if adversary.get_curr_host_id() not in adversary.get_compromised_hosts():
            adversary.get_compromised_hosts().append(adversary.get_curr_host_id())
            adversary.get_attack_stats().update_compromise_host(adversary.curr_host)
            logging.info("Adversary: Host %i has been compromised at %.1fs!" % (adversary.get_curr_host_id(), self.env.now))
            adversary.get_network().update_reachable_compromise(adversary.get_curr_host_id(), adversary.get_compromised_hosts())

            # update the user password list for next attack to try
            for user in adversary.get_curr_host().get_compromised_users():
                if user not in adversary.get_compromised_users():
                    adversary.get_attack_stats().update_compromise_user(user)
            adversary._compromised_users = list(set(adversary.get_compromised_users() + adversary.get_curr_host().get_compromised_users()))

    def recovery_a_node(self, node_id):
        """
        update some parameter about a node when it is set to uncompromised from conpromised
        """
        adversary = self.adversary
        if node_id in adversary.get_compromised_hosts():
            self.time_network.get_hosts()[node_id].compromised = False
            adversary.get_compromised_hosts().remove(node_id)
            logging.info("MTD: Host %i has been set to uncompromised at %.1fs!" % (node_id, self.env.now))
            adversary.get_network().update_reachable_compromise(node_id, adversary.get_compromised_hosts())
            # change the node color to normal color
            self.time_network.colour_map[node_id] = NODE_COLOURS[self.time_network.graph.nodes[node_id]['layer']]
            self.add_attacker_new_message(f"Message: Node {node_id} was set to uncompromised because some services on it has been changed")

    def update_network(self):
        """
        update the information about the network and the nodes in network
        """
        self.scale_x = 100
        self.scale_y = (self.height) // (self.time_network.max_y_pos - self.time_network.min_y_pos)
        self.shift_y = self.height - self.scale_y * self.time_network.max_y_pos

        pos_dict = self.time_network.pos
        for index in self.get_current_compromised_hosts():
            if self.time_network.colour_map[index] != 'red':
                # some node color has been refresh because of topological shuffling, we need to change it back according to the compromised list
                # logging.info(f"Change the node {index} color from {self.time_network.colour_map[index]} to red!")
                self.time_network.colour_map[index] = 'red'
        for index in self.target_node_num_list:
            if self.time_network.colour_map[index] != 'white':
                # logging.info(f"Change the target node {index} color from {self.time_network.colour_map[index]} to white!")
                self.time_network.colour_map[index] = 'white'

        color_list = self.time_network.colour_map
        self.nodes = []
        for key, color in zip(pos_dict, color_list):
            x = (pos_dict[key][0] * self.scale_x)
            y = (pos_dict[key][1] * self.scale_y) + self.shift_y
            self.nodes.append(Node(key, x, y, color))

    def start_real_time_simulation(self, period):
        # create a threading for real time simulation
        self.finished_event = threading.Event()
        self.real_time_thread = threading.Thread(target=self._real_time_simulation, args=(period,))
        self.real_time_thread.start()

    def _real_time_simulation(self, period):
        start_time = time.perf_counter()   # the number of second from one fix moment
        while self.isrunning:
            time.sleep(period)
            last_time = self.sim_time
            self.sim_time = time.perf_counter() - start_time  # update the simulation time
            # logging.info("Period from %.3f to %.3f" % (last_time, self.sim_time))
            if self.sim_time * SPEED_RATIO < GAME_TOTAL_TIME:
                self.env.run(until=self.sim_time * SPEED_RATIO)
            else:
                logging.info(f"Now the time out, the defenders win at {self.env.now:.1f}s!")
                self.winner = 'Defender'
                self.isrunning = False

            for node_id in self.target_node_num_list:
                if node_id in self.get_current_compromised_hosts():
                    logging.info(f"Now the target node has been compromised, the attackers win at {self.env.now:.1f}s!")
                    self.winner = 'Attacker'
                    self.isrunning = False

        self.finished_event.set()  # set the event when simulation stop
        logging.info("Simulation thread has stopped.")

    
    def execute_simulation(self, start_time=0, finish_time=None, scheme='random', mtd_interval=None, custom_strategies=None,
                        checkpoints=None, total_nodes=32, total_endpoints=5, total_subnets=8, total_layers=4,
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
        # if some error happen and the game mode or create role have not been set, automatically set it
        if self.get_game_mode() == None:
            self.set_game_mode('Computer')
        if self.get_creator_role() == None:
            self.set_creator_role('defender')
        logging.info(f"Game mode: {self.game_mode}; Creator role: {self.creator_role}")

        self.env = simpy.Environment()
        end_event = self.env.event()

        self.time_network = TimeNetwork(total_nodes=total_nodes, total_endpoints=total_endpoints,
                                total_subnets=total_subnets, total_layers=total_layers,
                                target_layer=target_layer, total_database=total_database,
                                terminate_compromise_ratio=terminate_compromise_ratio)

        self.adversary = Adversary(network=self.time_network, attack_threshold=ATTACKER_THRESHOLD)

        # init some game parameters and update network
        self.target_node_num_list = random.sample(range(TOTAL_NODE - 9, TOTAL_NODE - 1), TOTAL_TARGET_NODE_NUM)
        self.topo_shuffle_time = 0
        self.set_visible_hosts()
        self.set_visible_edges()
        self.scan_port_progress = [False for _ in range(TOTAL_NODE)]
        self.exploit_vuln_progress = [False for _ in range(TOTAL_NODE)]
        self.brute_force_progress = [True for _ in range(TOTAL_NODE)]
        self.attacker_new_message = deque()
        self.compromised_services = []
        self.update_network()   # get the position, color for all nodes and append them to self.nodes for frontend to access

        # start attack
        self.attack_operation = AttackOperation(env=self.env, end_event=end_event, adversary=self.adversary, proceed_time=0)
        if self.get_game_mode() == 'Computer' and self.get_creator_role() == 'defender':
            self.attack_operation.proceed_attack()

        # start mtd
        self.mtd_operation = MTDOperation(env=self.env, end_event=end_event, network=self.time_network, scheme=scheme,
                                    attack_operation=self.attack_operation, proceed_time=0,
                                    mtd_trigger_interval=mtd_interval, custom_strategies=custom_strategies)
        if self.get_game_mode() == 'Computer' and self.get_creator_role() == 'attacker':
            self.mtd_operation.proceed_mtd()

        # start simulation
        if finish_time is not None:
            self.env.run(until=(finish_time - start_time))
        else:
            # self.env.run(until=end_event)
            self.start_real_time_simulation(SIMULATION_INTERVAL)

    def start(self):
        self.isrunning = True
        self.execute_simulation(start_time=0, finish_time=None, mtd_interval=200, scheme='random', total_nodes=TOTAL_NODE, new_network=True)