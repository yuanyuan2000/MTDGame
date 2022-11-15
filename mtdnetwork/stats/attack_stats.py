import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
import os
import numpy as np


class AttackStatistics:
    def __init__(self):
        self._attack_operation_record = []

    def append_attack_operation_record(self, name, start_time, finish_time, adversary, interrupted_mtd=None):
        duration = finish_time - start_time
        interrupted_in = 'None'
        interrupted_by = 'None'
        if interrupted_mtd is not None:
            interrupted_in = interrupted_mtd.get_resource_type()
            interrupted_by = interrupted_mtd.get_name()
        self._attack_operation_record.append({
            'name': name,
            'start_time': start_time,
            'finish_time': finish_time,
            'duration': duration,
            'current_host': adversary.get_curr_host_id(),
            'current_host_attempt': adversary.get_attack_counter()[adversary.get_curr_host_id()],
            'cumulative_attempts': adversary.get_curr_attempts(),
            'cumulative_compromised_hosts': len(adversary.get_compromised_hosts()),
            'compromise_host': 'None',
            'compromise_users': [],
            'interrupted_in': interrupted_in,
            'interrupted_by': interrupted_by,
        })

    def update_compromise_host(self, curr_host_id):
        self._attack_operation_record[-1]['compromise_host'] = curr_host_id

    def update_compromise_user(self, user):
        self._attack_operation_record[-1]['compromise_users'].append(user)

    def get_record(self):
        return pd.DataFrame(self._attack_operation_record)

    def save_record(self, sim_time, scheme):
        current_directory = os.getcwd()
        if not os.path.exists(current_directory + '\\data_analysis'):
            os.makedirs(current_directory + '\\data_analysis')
        pd.DataFrame(self._attack_operation_record).to_csv('data_analysis/attack_operation_record_' +
                                                           str(sim_time) + '_' + scheme + '.csv', index=False)

    def mean_time_to_compromise(self):
        record = self.get_record()
        compromised_list = record[record['compromise_host'] != 'None']['compromise_host']
        compromise_time_list = []
        for host_id in compromised_list:
            action_list = record[record['current_host'] == host_id]
            compromise_time = max(action_list['finish_time']) - min(action_list['start_time'])
            compromise_time_list.append(compromise_time)
        return np.mean(compromise_time_list)

    # def get_compromised_attack_operation_counts(self):
    #     record = pd.DataFrame(self._attack_operation_record)
    #     return record[~record['compromise_host'].isnull()]['name'].str.split(
    #         expand=True).stack().value_counts().reset_index().rename(columns={'index': 'name', 0: 'frequency'})

    def visualise_attack_operation_group_by_host(self):
        attack_operation_record = self.get_record()
        fig, ax = plt.subplots(1, figsize=(16, 5))
        colors = ['purple', 'blue', 'green', 'yellow', 'orange', 'red']
        attack_action_legend = []
        attack_action_legend_name = []
        for i, v in enumerate(attack_operation_record['name'].unique()):
            attack_operation_record.loc[attack_operation_record.name == v, 'color'] = colors[i]
            attack_action_legend.append(Line2D([0], [0], color=colors[i], lw=4))
            attack_action_legend_name.append(v)

        ax.barh(attack_operation_record['current_host'].astype(str), attack_operation_record['duration'],
                left=attack_operation_record['start_time'], height=0.4, color=attack_operation_record['color'])

        ax.legend(attack_action_legend, attack_action_legend_name, loc='lower left')
        plt.gca().invert_yaxis()
        plt.xlabel('Time', weight='bold', fontsize=18)
        plt.ylabel('Target Host', weight='bold', fontsize=18)
        fig.tight_layout()
        plt.savefig('data_analysis/attack_action_record_group_by_host.png')
        plt.show()

    def visualise_attack_operation(self):
        attack_operation_record = self.get_record()
        fig, ax = plt.subplots(1, figsize=(16, 5))
        ax.barh(attack_operation_record['name'], attack_operation_record['duration'],
                left=attack_operation_record['start_time'], height=0.1, zorder=1)

        interrupted_record = attack_operation_record[attack_operation_record['interrupted_in'] != 'None']
        interrupted_record['color'] = np.where(interrupted_record['interrupted_in'] == 'network', 'green', 'orange')
        ax.scatter(interrupted_record['finish_time'], interrupted_record['name'], color=interrupted_record['color'],
                   zorder=3)

        compromise_record = attack_operation_record[attack_operation_record['compromise_host'] != 'None']
        ax.scatter(compromise_record['finish_time'], compromise_record['name'], color='red', zorder=2)

        custom_lines_attack = [Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=10),
                               Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markersize=10),
                               Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10), ]

        ax.legend(custom_lines_attack, ['network layer MTD', 'application layer MTD', 'compromise host'],
                  loc='upper right')

        plt.gca().invert_yaxis()
        plt.xlabel('Time', weight='bold', fontsize=18)
        plt.ylabel('Attack Progress', weight='bold', fontsize=18)
        fig.tight_layout()
        plt.savefig('data_analysis/attack_record.png')
        plt.show()

    def compromised_record_by_attack_action(self, action):
        attack_operation_record = self.get_record()
        return attack_operation_record[(attack_operation_record['name'] == action) &
                                       (attack_operation_record['compromise_host'] != 'None')]
