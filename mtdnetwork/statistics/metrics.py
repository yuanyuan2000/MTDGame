import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


class Metrics:
    def __init__(self, mtd_record, attack_record):
        self._mtd_record = mtd_record
        self._attack_record = attack_record

    def mtd_execute_frequency(self):
        """
        The frequency of executing MTDs
        :return: Total number of executed MTD / Elapsed time
        """
        if len(self._mtd_record) == 0:
            return 0
        record = self._mtd_record
        return len(record) / (record.iloc[-1]['finish_time'] - record.iloc[0]['start_time'])

    def mean_time_to_compromise(self):
        """
        The mean time to compromise a host

        ATTACK_ACTION: SCAN_PORT, EXPLOIT_VULN, BRUTE_FORCE
        Elapsed time on a compromised host = The sum of the time duration of one or more ATTACK_ACTIONs on the host
        :return: the average time spent on compromise a host
        """
        record = self._attack_record
        compromised_list = record[record['compromise_host_uuid'] != 'None']['compromise_host_uuid'].unique()
        compromise_time_list = []
        for host_uuid in compromised_list:
            action_list = record[(record['current_host_uuid'] == host_uuid) &
                                 (record['name'].isin(['SCAN_PORT', 'EXPLOIT_VULN', 'BRUTE_FORCE']))]
            compromise_time = action_list['duration'].sum()
            compromise_time_list.append(compromise_time)
        return np.mean(compromise_time_list)

    def compromise_record_by_attack_action(self, action):
        """
        :return: a list of attack record that contains hosts compromised by the given action
        """
        record = self._attack_record
        return record[(record['name'] == action) &
                      (record['compromise_host'] != 'None')]

    def visualise_attack_operation_group_by_host(self):
        """
        visualise the action flow of attack operation group by host ids.
        """
        record = self._attack_record
        fig, ax = plt.subplots(1, figsize=(16, 5))
        colors = ['purple', 'blue', 'green', 'yellow', 'orange', 'red']
        attack_action_legend = []
        attack_action_legend_name = []
        for i, v in enumerate(record['name'].unique()):
            record.loc[record.name == v, 'color'] = colors[i]
            attack_action_legend.append(Line2D([0], [0], color=colors[i], lw=4))
            attack_action_legend_name.append(v)

        ax.barh(record['current_host'].astype(str), record['duration'],
                left=record['start_time'], height=0.4, color=record['color'])

        ax.legend(attack_action_legend, attack_action_legend_name, loc='lower left')
        plt.gca().invert_yaxis()
        plt.xlabel('Time', weight='bold', fontsize=18)
        plt.ylabel('Target Host', weight='bold', fontsize=18)
        fig.tight_layout()
        plt.savefig('data_analysis/attack_action_record_group_by_host.png')
        plt.show()

    def visualise_attack_operation(self):
        """
        visualise the action flow of attack operation
        """
        record = self._attack_record
        fig, ax = plt.subplots(1, figsize=(16, 5))
        ax.barh(record['name'], record['duration'],
                left=record['start_time'], height=0.1, zorder=1)

        interrupted_record = record[record['interrupted_in'] != 'None']
        interrupted_record['color'] = np.where(interrupted_record['interrupted_in'] == 'network', 'green', 'orange')
        ax.scatter(interrupted_record['finish_time'], interrupted_record['name'], color=interrupted_record['color'],
                   zorder=3)

        compromise_record = record[record['compromise_host'] != 'None']
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

    def visualise_mtd_operation(self):
        """
        visualise the action flow of mtd operation
        """
        if len(self._mtd_record) == 0:
            return
        record = self._mtd_record
        fig, ax = plt.subplots(1, figsize=(16, 6))
        colors = ['blue', 'green', 'orange']
        mtd_action_legend = []
        mtd_action_legend_name = []
        for i, v in enumerate(record['executed_at'].unique()):
            record.loc[record['executed_at'] == v, 'color'] = colors[i]
            mtd_action_legend.append(Line2D([0], [0], color=colors[i], lw=4))
            mtd_action_legend_name.append(v)
        ax.barh(record['name'].astype(str), record['duration'],
                left=record['start_time'], height=0.4, color=record['color'])
        ax.legend(mtd_action_legend, mtd_action_legend_name, loc='lower right')
        plt.gca().invert_yaxis()
        plt.xlabel('Time', weight='bold', fontsize=18)
        plt.ylabel('MTD Techniques', weight='bold', fontsize=18)
        fig.tight_layout()
        plt.savefig('data_analysis/mtd_record.png')
        plt.show()
