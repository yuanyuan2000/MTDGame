import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx
import pandas as pd
import os
directory = os.getcwd()

class Evaluation:
    def __init__(self, network, adversary):

        self._network = network
        self._adversary = adversary
        self._mtd_record = network.get_mtd_stats().get_record()
        self._attack_record = adversary.get_attack_stats().get_record()

    def compromised_num(self):
        record = self._attack_record
        compromised_hosts = record[record['compromise_host_uuid'] != 'None']['compromise_host_uuid'].unique()
        return len(compromised_hosts)

    def compromised_num_by_timestamp(self, timestamp):
        record = self._attack_record
        compromised_hosts = record[(record['compromise_host_uuid'] != 'None') &
                                   (record['finish_time'] <= timestamp)]['compromise_host_uuid'].unique()
        return len(compromised_hosts)

    def mtd_execution_frequency(self):
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
        Attack action time = The sum of the time duration of all ATTACK_ACTION
        :return: the average time spent to compromise a host
        """
        record = self._attack_record
        compromised_num = self.compromised_num()
        # Elapsed time on a compromised host = The sum of the time duration of one or more ATTACK_ACTIONs on the host
        # compromise_time_list = []
        # for host_uuid in compromised_hosts:
        #     action_list = record[(record['current_host_uuid'] == host_uuid) &
        #                          (record['name'].isin(['SCAN_PORT', 'EXPLOIT_VULN', 'BRUTE_FORCE']))]
        #     compromise_time = action_list['duration'].sum()
        #     compromise_time_list.append(compromise_time)
        # return np.mean(compromise_time_list)
        attack_action_time = record[record['name'].isin(['SCAN_PORT', 'EXPLOIT_VULN', 'BRUTE_FORCE'])]['duration'].sum()
        return np.mean(attack_action_time / compromised_num)

    def mean_time_to_compromise_10_timestamp(self):
        record = self._attack_record
        step = max(record['finish_time']) / 10
        MTTC = []
        for i in range(1, 11, 1):
            compromised_num = self.compromised_num_by_timestamp(step * i)
            if compromised_num == 0:
                continue
            attack_action_time = record[(record['name'].isin(['SCAN_PORT', 'EXPLOIT_VULN', 'BRUTE_FORCE'])) &
                                        (record['finish_time'] <= step * i)]['duration'].sum()
            MTTC.append({'Mean Time to Compromise': np.mean(attack_action_time / compromised_num), 'Time': step * i})

        return MTTC

    def attack_success_rate(self):
        # """
        # :return: number of compromised hosts / number of attempted hosts
        # """
        # record = self._attack_record
        # attempt_hosts = record[record['current_host_uuid'] != -1]['current_host_uuid'].unique()
        # compromised_hosts = record[record['compromise_host_uuid'] != 'None']['compromise_host_uuid'].unique()
        # return len(compromised_hosts) / len(attempt_hosts)
        record = self._attack_record
        attempt_hosts = record[record['current_host_uuid'] != -1]['current_host_uuid'].unique()
        compromised_hosts = record[record['compromise_host_uuid'] != 'None']['compromise_host_uuid'].unique()
        attack_actions = record[record['name'].isin(['SCAN_PORT', 'EXPLOIT_VULN', 'BRUTE_FORCE'])]
        attack_event_num = 0
        for host in attempt_hosts:
            attack_event_num += len(attack_actions[(attack_actions['current_host_uuid'] == host) &
                                                   (attack_actions['name'] == 'SCAN_PORT')])
        return len(compromised_hosts) / attack_event_num

    def compromise_record_by_attack_action(self, action):
        """
        :return: a list of attack record that contains hosts compromised by the given action
        """
        record = self._attack_record
        return record[(record['name'] == action) &
                      (record['compromise_host'] != 'None')]

    def draw_network(self):
        """
        Draws the topology of the network while also highlighting compromised and exposed endpoint nodes.
        """
        plt.figure(1, figsize=(15, 12))
        nx.draw(self._network.graph, pos=self._network.pos, node_color=self._network.colour_map, with_labels=True)
        plt.savefig(directory+'/experimental_data/network.png')
        plt.show()

    def draw_hacker_visible(self):
        """
        Draws the network that is visible for the hacker
        """
        subgraph = self._network.get_hacker_visible_graph()
        plt.figure(1, figsize=(15, 12))
        nx.draw(subgraph, pos=self._network.pos, with_labels=True)
        plt.show()

    def draw_compromised(self):
        """
        Draws the network of compromised hosts
        """
        compromised_hosts = self._adversary.get_compromised_hosts()
        subgraph = self._network.graph.subgraph(compromised_hosts)
        colour_map = []
        c_hosts = sorted(compromised_hosts)
        for node_id in c_hosts:
            if node_id in self._network.exposed_endpoints:
                colour_map.append("green")
            else:
                colour_map.append("red")

        plt.figure(1, figsize=(15, 12))
        nx.draw(subgraph, pos=self._network.pos, node_color=colour_map, with_labels=True)
        plt.show()

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

        hosts = record['current_host_uuid'].unique()
        host_token = [str(x) for x in range(len(hosts))]
        for i, v in enumerate(hosts):
            record.loc[record['current_host_uuid'] == v, 'curr_host_token'] = host_token[i]

        ax.barh(record['curr_host_token'], record['duration'],
                left=record['start_time'], height=0.4, color=record['color'])

        ax.legend(attack_action_legend, attack_action_legend_name, loc='lower left')
        plt.gca().invert_yaxis()
        plt.xlabel('Time', weight='bold', fontsize=18)
        plt.ylabel('Hosts', weight='bold', fontsize=18)
        fig.tight_layout()
        plt.savefig(directory+'/experimental_data/attack_action_record_group_by_host.png')
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
        print("total compromised hosts: ", len(compromise_record))
        ax.scatter(compromise_record['finish_time'], compromise_record['name'], color='red', zorder=2)

        custom_lines_attack = [Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=10),
                               Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markersize=10),
                               Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10), ]

        ax.legend(custom_lines_attack, ['network layer MTD', 'application layer MTD', 'compromise host'],
                  loc='upper right')

        plt.gca().invert_yaxis()
        plt.xlabel('Time', weight='bold', fontsize=18)
        plt.ylabel('Attack Actions', weight='bold', fontsize=18)
        fig.tight_layout()
        plt.savefig(directory+'/experimental_data/attack_record.png')
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
        plt.ylabel('MTD Strategies', weight='bold', fontsize=18)
        fig.tight_layout()
        plt.savefig(directory+'/experimental_data/mtd_record.png')
        plt.show()

    def get_network(self):
        return self._network
