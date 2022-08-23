import mtdnetwork.targetnetwork as targetnetwork
import mtdnetwork.copynetwork as copynetwork
import mtdnetwork.hacker as hacker
import mtdnetwork.constants as constants

import numpy as np

from mtdnetwork.mtd.portshuffle import PortShuffle
from mtdnetwork.mtd.ipshuffle import IPShuffle
from mtdnetwork.mtd.osdiversity import OSDiversity
from mtdnetwork.mtd.servicediversity import ServiceShuffle
from mtdnetwork.mtd.usershuffle import UserShuffle
from mtdnetwork.mtd.hosttopologyshuffle import HostTopologyShuffle
from mtdnetwork.mtd.completetopologyshuffle import CompleteTopologyShuffle

import logging, argparse, json
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
    generic_network = copynetwork.Network(graph, pos, colour_map,200, 20, 20, 5)

    mtd_strategies = []

    if args.mtd:
        mtd_strategies = [strat_str.lower() for strat_str in args.mtd.split(',')]

    if "portshuffle" in mtd_strategies:
        target_network.register_mtd(PortShuffle)
        generic_network.register_mtd(PortShuffle)

    if "ipshuffle" in mtd_strategies:
        target_network.register_mtd(IPShuffle)
        generic_network.register_mtd(IPShuffle)

    if "osshuffle" in mtd_strategies:
        target_network.register_mtd(OSDiversity)
        generic_network.register_mtd(OSDiversity)

    if "serviceshuffle" in mtd_strategies:
        target_network.register_mtd(ServiceShuffle)
        generic_network.register_mtd(ServiceShuffle)

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
    error_threshold = constants.STANDARD_ERROR_BENCHMARK
    target_error_threshold_met = False
    generic_error_threshold_met = False
    target_results = []
    generic_results = []
    nHost_compromised = []
    attack_attempts = []


    while (target_error_threshold_met == False) and (generic_error_threshold_met == False):
        # Target Network Creation + Attacker, running one simulation
        target_network, generic_network = create_network(args)
        if target_error_threshold_met == False:
            target_adversary = hacker.Hacker(target_network, constants.ATTACKER_THRESHOLD)
            final_time = 0
            for curr_time in range(0, args.time, TIME_STEP):
                target_network.step(curr_time)
                target_adversary.step(curr_time)
                final_time = curr_time
                if target_adversary.done:
                    break
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
            generic_adversary = hacker.Hacker(generic_network, constants.ATTACKER_THRESHOLD)
            final_time = 0
            for curr_time in range(0, args.time, TIME_STEP):
                generic_network.step(curr_time)
                generic_adversary.step(curr_time)
                final_time = curr_time
                if generic_adversary.done:
                    break
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

        if target_error < error_threshold:
            target_file_name = "Target " + args.output
            target_data = open(target_file_name, "w")
            json.dump(target_results, target_data)
            target_data.close()
            print("Target Network has completed")

        if generic_error < error_threshold:
            generic_file_name = "Generic " + args.output
            generic_data = open(generic_file_name, "w")
            json.dump(generic_results, generic_data)
            generic_data.close()
            print("Generic Network has completed")

        print("DONE!")

if __name__ == "__main__":
    main()