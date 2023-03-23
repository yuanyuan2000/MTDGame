import os
import sys

current_directory = os.getcwd()
if not os.path.exists(current_directory + '\\experimental_data'):
    os.makedirs(current_directory + '\\experimental_data')
    os.makedirs(current_directory + '\\experimental_data\\plots')
    os.makedirs(current_directory + '\\experimental_data\\results')
sys.path.append(current_directory.replace('experiments', ''))
import warnings
import pandas as pd
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
plt.set_loglevel('WARNING')
from run import dap_mtd_simulation, construct_average_result, execute_multithreading

results = execute_multithreading(dap_mtd_simulation, iterations=10, num_threads=5)

# results = []
# result = dap_mtd_simulation()
# results.append(result)

results_avg = construct_average_result(results)

pd.DataFrame(results_avg).to_csv('experimental_data/results/dap_mtd_sim.csv', index=False)
