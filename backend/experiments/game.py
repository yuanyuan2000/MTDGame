

def start():
    import os
    import sys
    current_directory = os.getcwd()
    experimental_path = os.path.join(current_directory, 'experiments')
    experimental_data_path = os.path.join(experimental_path, 'experimental_data')
    if not os.path.exists(experimental_data_path):
        os.makedirs(experimental_data_path)
        plots_path = os.path.join(experimental_data_path, 'plots')
        os.makedirs(plots_path)
        results_path = os.path.join(experimental_data_path, 'results')
        os.makedirs(results_path)
    sys.path.append(current_directory.replace('experiments', ''))

    import warnings
    import matplotlib.pyplot as plt
    warnings.filterwarnings("ignore")
    plt.set_loglevel('WARNING')
    from experiments.run import execute_simulation, create_experiment_snapshots
    from mtdnetwork.mtd.completetopologyshuffle import CompleteTopologyShuffle
    from mtdnetwork.mtd.ipshuffle import IPShuffle
    from mtdnetwork.mtd.hosttopologyshuffle import HostTopologyShuffle
    from mtdnetwork.mtd.portshuffle import PortShuffle
    from mtdnetwork.mtd.osdiversity import OSDiversity
    from mtdnetwork.mtd.servicediversity import ServiceDiversity
    from mtdnetwork.mtd.usershuffle import UserShuffle
    from mtdnetwork.mtd.osdiversityassignment import OSDiversityAssignment
    import logging

    logging.basicConfig(format='%(message)s', level=logging.INFO)

    create_experiment_snapshots([25, 50, 75, 100])

    evaluation = execute_simulation(start_time=0, finish_time=3000, mtd_interval=200, scheme='random', total_nodes=100)

start()