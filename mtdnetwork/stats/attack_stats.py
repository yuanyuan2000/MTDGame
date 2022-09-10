class AttackStatistics:
    def __init__(self):
        self.attack_operation_record = []

    def append_attack_operation_record(self, name, start_time, finish_time, adversary):
        duration = finish_time - start_time
        interrupted_in = ''
        interrupted_by = ''
        if adversary.interrupted_mtd is not None:
            interrupted_in = adversary.interrupted_mtd.resource
            interrupted_by = adversary.interrupted_mtd.name
        self.attack_operation_record.append({
            'name': name,
            'start_time': start_time,
            'finish_time': finish_time,
            'duration': duration,
            'interrupted_in': interrupted_in,
            'interrupted_by': interrupted_by,
            'current_host': adversary.curr_host_id,
            'current_host_attempt': adversary.attack_counter[adversary.curr_host_id],
            'cumulative_attempts': adversary.curr_attempts,
            'compromise_host': '',
            'cumulative_compromised_hosts': len(adversary.compromised_hosts),
            'cumulative_compromised_vulns': adversary.total_vuln_compromise
        })

    def update_compromise_host(self, curr_host_id):
        self.attack_operation_record[-1]['compromise_host'] = curr_host_id
