import mtdnetwork.targetnetwork as targetnetwork
import mtdnetwork.copynetwork as copynetwork
import mtdnetwork.hacker as hacker
import mtdnetwork.constants as constants

import numpy as np

from mtdnetwork.mtd.portshuffle import PortShuffle
from mtdnetwork.mtd.ipshuffle import IPShuffle
from mtdnetwork.mtd.osdiversity import OSDiversity
from mtdnetwork.mtd.servicediversity import ServiceDiversity
from mtdnetwork.mtd.usershuffle import UserShuffle
from mtdnetwork.mtd.hosttopologyshuffle import HostTopologyShuffle
from mtdnetwork.mtd.completetopologyshuffle import CompleteTopologyShuffle

import logging, argparse, json, time
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

TIME_STEP = 1
NO_MTD_SCAN_TYPE = "None"

def parse_args():
    parser = argparse.ArgumentParser(description="Run a MTD simulation")

    parser.add_argument(
        "-m", "--mtd",
        help="A comma seperated list of the MTD strategies to use",
        type = str
    )

    parser.add_argument(
        "-n", "--nodes",
        help = "The number of nodes in the network.",
        default = 200,
        type = int
    )

    parser.add_argument(
        "-e", "--endpoints",
        help="The number of exposed endpoints that are initially exposed to the hacker",
        default=20,
        type = int
    )

    parser.add_argument(
        "-s", "--subnets",
        help="The number of subnets in the network.",
        default=20,
        type = int
    )
    
    parser.add_argument(
        "-l", "--layers",
        help="The number of layers in the subnet including the exposed endpoint layer",
        default = 5,
        type = int
    )

    parser.add_argument(
        "-tar", "--target",
        help = "The layer of the target node",
        default = 3,
        type = int
    )


    parser.add_argument(
        "-t", "--time",
        help = "The total simulation time",
        default = 1000000,
        type = int
    )

    parser.add_argument(
        "output",
        help="The JSON output filename",
        type = str
    )

    return parser.parse_args()

def create_network(args):
    target_network = targetnetwork.Network(args.nodes, args.endpoints, args.subnets, args.layers, args.target)
    graph = target_network.get_graph_copy()
    colour_map = target_network.get_colourmap()
    pos = target_network.get_pos()
    node_per_layer = target_network.get_node_per_layer()
    users_list = target_network.get_users_list()
    users_per_host = target_network.get_users_per_host()
    generic_network = copynetwork.Network(graph, pos, colour_map,args.nodes, args.endpoints, args.subnets, args.layers, node_per_layer, users_list, users_per_host)

    mtd_strategies = []

    if args.mtd:
        mtd_strategies = [strat_str.lower() for strat_str in args.mtd.split(',')]

    if "portshuffle" in mtd_strategies:
        target_network.register_mtd(PortShuffle)
        generic_network.register_mtd(PortShuffle)

    if "ipshuffle" in mtd_strategies:
        target_network.register_mtd(IPShuffle)
        generic_network.register_mtd(IPShuffle)

    if "osdiversity" in mtd_strategies:
        target_network.register_mtd(OSDiversity)
        generic_network.register_mtd(OSDiversity)

    if "servicediversity" in mtd_strategies:
        target_network.register_mtd(ServiceDiversity)
        generic_network.register_mtd(ServiceDiversity)

    if "usershuffle" in mtd_strategies:
        target_network.register_mtd(UserShuffle)
        generic_network.register_mtd(UserShuffle)

    if "hosttopologyshuffle" in mtd_strategies:
        target_network.register_mtd(HostTopologyShuffle)
        generic_network.register_mtd(HostTopologyShuffle)

    if "completetopologyshuffle" in mtd_strategies:
        target_network.register_mtd(CompleteTopologyShuffle)
        generic_network.register_mtd(CompleteTopologyShuffle)

    return [target_network, generic_network]

def main():
    args = parse_args()
    target_error_threshold = constants.STANDARD_ERROR_BENCHMARK_PERCENT * args.nodes / 100
    generic_error_threshold = constants.STANDARD_ERROR_BENCHMARK_PERCENT * args.nodes * constants.ATTACKER_THRESHOLD / 100
    print(target_error_threshold, generic_error_threshold)
    target_error_threshold_met = False
    generic_error_threshold_met = False
    target_results = []
    generic_results = []
    nHost_compromised = []
    attack_attempts = []
    counter = 1

    target_file_name = "Target-" + args.output
    generic_file_name = "Generic-" + args.output
    print(target_file_name, generic_file_name)
    
    # Used when data thresholding is used
    # while (target_error_threshold_met == False) and (generic_error_threshold_met == False):
    
    # Used when network is run x amount of times
    while (counter < 3):

        # Target Network Creation + Attacker, running one simulation
        target_network, generic_network = create_network(args)
        target_adversary = hacker.Hacker(target_network, constants.ATTACKER_THRESHOLD)
        generic_adversary = hacker.Hacker(generic_network, constants.ATTACKER_THRESHOLD)
        # Added to make sure network + hacker is fully initialised before network is run
        time.sleep(3)
        if target_error_threshold_met == False:
            final_time = 0
            for curr_time in range(0, args.time, TIME_STEP):
                target_network.step(curr_time)
                target_adversary.step(curr_time)
                final_time = curr_time
                if target_adversary.done:
                    break
            print("TARGET DONE!")
            network_results = target_network.get_statistics()
            network_results["Complete Time"] = final_time
            if args.mtd:
                network_results["Simulation Type"] = args.mtd
            else:
                network_results["Simulation Type"] = NO_MTD_SCAN_TYPE
            nHost_compromised.append(len(target_adversary.get_compromised()))
            target_results.append(target_adversary.get_statistics())
            target_results.append(network_results)
        
        # Generic Network Creation + Attacker, running one simulation
        # NOTE: Since this copies the target_network, it needs target_network initialised
        if generic_error_threshold_met == False:  
            final_time = 0
            for curr_time in range(0, args.time, TIME_STEP):
                generic_network.step(curr_time)
                generic_adversary.step(curr_time)
                final_time = curr_time
                if generic_adversary.done:
                    break
            print("GENERIC DONE!")
            network_results = generic_network.get_statistics()
            network_results["Complete Time"] = final_time
            if args.mtd:
                network_results["Simulation Type"] = args.mtd
            else:
                network_results["Simulation Type"] = NO_MTD_SCAN_TYPE
            attack_attempts.append(generic_adversary.get_attack_attempts())
            generic_results.append(generic_adversary.get_statistics())
            generic_results.append(network_results)
        
        target_error = np.std(nHost_compromised, ddof=1) / np.sqrt(np.size(nHost_compromised))
        generic_error = np.std(attack_attempts, ddof=1) / np.sqrt(np.size(attack_attempts))
        print("Target Error: ", target_error, "nhost: ", nHost_compromised)
        print("Generic Error: ", generic_error, "attack attempts: ", attack_attempts)

        # Saves all data into one file if error threshold is met or if its run over 100 times and stops running that network (Alternative is code below)
        # if (target_error_threshold_met == False):
        #     # if (target_error < target_error_threshold) or (len(nHost_compromised) > 100):
        #     if (len(nHost_compromised) > 100):
        #         target_data = open(target_file_name, "w")
        #         json.dump(target_results, target_data)
        #         target_data.close()
        #         print("Target Network has completed")
        #         target_error_threshold_met = True

        # if (generic_error_threshold_met == False):
        #     # if (generic_error < generic_error_threshold) or (len(attack_attempts) > 100):
        #     if (len(attack_attempts) > 100):
        #         generic_data = open(generic_file_name, "w")
        #         json.dump(generic_results, generic_data)
        #         generic_data.close()
        #         print("Generic Network has completed")
        #         generic_error_threshold_met = True

        # Saves the data of each run individually, used when network is run x amount of times

        target_file_name = str(counter) + "-Target-" + args.output 
        generic_file_name = str(counter) + "-Generic-" + args.output
        
        generic_data = open(generic_file_name, "w")
        json.dump(generic_results, generic_data)
        generic_data.close()
        print("Generic Network has completed run ", counter)
        
        target_data = open(target_file_name, "w")
        json.dump(target_results, target_data)
        target_data.close()
        print("Target Network has completed run ", counter)

        target_results = []
        generic_results = []

        counter += 1
        

if __name__ == "__main__":
    main()