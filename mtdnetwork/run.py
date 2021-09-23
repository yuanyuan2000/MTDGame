import mtdnetwork.network as network
import mtdnetwork.hacker as hacker

from mtdnetwork.mtd.portshuffle import PortShuffle
from mtdnetwork.mtd.ipshuffle import IPShuffle
from mtdnetwork.mtd.osshuffle import OSShuffle
from mtdnetwork.mtd.serviceshuffle import ServiceShuffle
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
        default=50,
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
        default = 3,
        type = int
    )

    parser.add_argument(
        "-t", "--time",
        help = "The total simulation time",
        default = 250000,
        type = int
    )

    parser.add_argument(
        "output",
        help="The JSON output filename",
        type = str
    )

    return parser.parse_args()

def create_network(args):
    sim_network = network.Network(args.nodes, args.endpoints, args.subnets, args.layers)

    mtd_strategies = []

    if args.mtd:
        mtd_strategies = [strat_str.lower() for strat_str in args.mtd.split(',')]

    if "portshuffle" in mtd_strategies:
        sim_network.register_mtd(PortShuffle)

    if "ipshuffle" in mtd_strategies:
        sim_network.register_mtd(IPShuffle)

    if "osshuffle" in mtd_strategies:
        sim_network.register_mtd(OSShuffle)

    if "serviceshuffle" in mtd_strategies:
        sim_network.register_mtd(ServiceShuffle)

    if "usershuffle" in mtd_strategies:
        sim_network.register_mtd(UserShuffle)

    if "hosttopologyshuffle" in mtd_strategies:
        sim_network.register_mtd(HostTopologyShuffle)

    if "completetopologyshuffle" in mtd_strategies:
        sim_network.register_mtd(CompleteTopologyShuffle)

    return sim_network

def main():
    args = parse_args()
    sim_network = create_network(args)
    adversary = hacker.Hacker(sim_network)

    final_time = 0
    for curr_time in range(0, args.time, TIME_STEP):
        sim_network.step(curr_time)
        adversary.step(curr_time)
        final_time = curr_time
        if adversary.done:
            break

    results = sim_network.get_statistics()
    results["Complete Time"] = final_time
    if args.mtd:
        results["Simulation Type"] = args.mtd
    else:
        results["Simulation Type"] = NO_MTD_SCAN_TYPE

    with open(args.output, "w") as f:
        json.dump(results, f)

    print("DONE!")

if __name__ == "__main__":
    main()