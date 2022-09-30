import pandas as pd


class AttackStatistics:
    def __init__(self):
        self.attack_operation_record = []

    def append_attack_operation_record(self, name, start_time, finish_time, adversary, interrupted_mtd=None):
        duration = finish_time - start_time
        interrupted_in = 'None'
        interrupted_by = 'None'
        if interrupted_mtd is not None:
            interrupted_in = interrupted_mtd.get_resource_type()
            interrupted_by = interrupted_mtd.get_name()
        self.attack_operation_record.append({
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
        self.attack_operation_record[-1]['compromise_host'] = curr_host_id

    def update_compromise_user(self, user):
        self.attack_operation_record[-1]['compromise_users'].append(user)

    def get_record(self):
        return self.attack_operation_record

    def get_compromised_attack_operation_counts(self):
        record = pd.DataFrame(self.attack_operation_record)
        return record[~record['compromise_host'].isnull()]['name'].str.split(
            expand=True).stack().value_counts().reset_index().rename(columns={'index': 'name', 0: 'frequency'})
