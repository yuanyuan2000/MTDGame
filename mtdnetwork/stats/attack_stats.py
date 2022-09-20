import pandas as pd

class AttackStatistics:
    def __init__(self):
        self.attack_operation_record = []

    def append_attack_operation_record(self, name, start_time, finish_time, adversary):
        duration = finish_time - start_time
        interrupted_in = ''
        interrupted_by = ''
        if adversary.interrupted_mtd is not None:
            interrupted_in = adversary.interrupted_mtd.resource_type
            interrupted_by = adversary.interrupted_mtd.name
        self.attack_operation_record.append({
            'name': name,
            'start_time': start_time,
            'finish_time': finish_time,
            'duration': duration,
            'current_host': adversary.curr_host_id,
            'current_host_attempt': adversary.attack_counter[adversary.curr_host_id],
            'cumulative_attempts': adversary.curr_attempts,
            'cumulative_compromised_hosts': len(adversary.compromised_hosts),
            'compromise_host': '',
            'compromise_users': [],
            'interrupted_in': interrupted_in,
            'interrupted_by': interrupted_by,
        })

    def update_compromise_host(self, curr_host_id):
        self.attack_operation_record[-1]['compromise_host'] = curr_host_id

    def update_compromise_user(self, user):
        self.attack_operation_record[-1]['compromise_users'].append(user)

    def get_record(self):
        return self.attack_operation_record

    def get_compromised_attack_operation_counts(self):
        record = pd.DataFrame(self.attack_operation_record)
        return record[~record['compromise_host'].isnull()]['name'].str.split(
            expand=True).stack().value_counts().reset_index().rename(columns={'index': 'name', 0: 'frequency'})
