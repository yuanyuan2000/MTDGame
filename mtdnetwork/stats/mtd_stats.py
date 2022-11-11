import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
import os


class MTDStatistics:
    def __init__(self):
        self._mtd_operation_record = []
        self._total_suspended = 0
        self._total_triggered = 0
        self._total_executed = 0
        self._total_attack_interrupted = 0
        self._switch_mtd_interval_at = {}
        self._switch_mtd_strategy_at = {}

    def append_mtd_operation_record(self, mtd_strategy, start_time, finish_time, duration):
        self._mtd_operation_record.append({
            'name': mtd_strategy.get_name(),
            'start_time': start_time,
            'finish_time': finish_time,
            'duration': duration,
            'executed_at': mtd_strategy.get_resource_type()
        })
        self._total_executed += 1

    def append_mtd_interval_record(self, timestamp, mtd_interval):
        self._switch_mtd_interval_at[timestamp] = mtd_interval

    def append_mtd_strategy_record(self, timestamp, mtd_strategy):
        self._switch_mtd_strategy_at[timestamp] = mtd_strategy

    def dict(self):
        return {
            'Total suspended MTD': self._total_suspended,
            'Total executed MTD': self._total_executed,
            'Total attack interrupted': self._total_attack_interrupted,
            'Switch MTD interval at': self._switch_mtd_interval_at,
            'Switch MTD strategy at': self._switch_mtd_strategy_at
        }

    def add_total_attack_interrupted(self):
        self._total_attack_interrupted += 1

    def add_total_suspended(self):
        self._total_suspended += 1

    def add_total_triggered(self):
        self._total_triggered += 1

    def get_record(self):
        return pd.DataFrame(self._mtd_operation_record)

    def save_record(self, sim_time, scheme):
        current_directory = os.getcwd()
        if not os.path.exists(current_directory + '\\data_analysis'):
            os.makedirs(current_directory + '\\data_analysis')
        pd.DataFrame(self._mtd_operation_record).to_csv('data_analysis/mtd_operation_record_' +
                                                        str(sim_time) + '_' + scheme + '.csv', index=False)

    def visualise_mtd_operation(self, scheme):
        mtd_operation_record = pd.DataFrame(self._mtd_operation_record)
        fig, ax = plt.subplots(1, figsize=(16, 6))
        colors = ['blue', 'green', 'orange']
        mtd_action_legend = []
        mtd_action_legend_name = []
        for i, v in enumerate(mtd_operation_record['executed_at'].unique()):
            mtd_operation_record.loc[mtd_operation_record['executed_at'] == v, 'color'] = colors[i]
            mtd_action_legend.append(Line2D([0], [0], color=colors[i], lw=4))
            mtd_action_legend_name.append(v)
        ax.barh(mtd_operation_record['name'].astype(str), mtd_operation_record['duration'],
                left=mtd_operation_record['start_time'], height=0.4, color=mtd_operation_record['color'])
        ax.legend(mtd_action_legend, mtd_action_legend_name, loc='lower right')
        plt.gca().invert_yaxis()
        plt.xlabel('Time', weight='bold', fontsize=18)
        plt.ylabel('MTD Techniques', weight='bold', fontsize=18)
        fig.tight_layout()
        plt.savefig('data_analysis/mtd_record_' + scheme + '.png')
        plt.show()
