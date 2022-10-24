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
            'executed_at': mtd_strategy.get_resource_type(),
            'batch_register_number': mtd_strategy.get_batch_register_number()
        })
        self._total_executed += 1

    def append_mtd_interval_record(self, timestamp, mtd_interval):
        self._switch_mtd_interval_at[timestamp] = mtd_interval

    def append_mtd_strategy_record(self, timestamp, mtd_strategy):
        self._switch_mtd_strategy_at[timestamp] = mtd_strategy

    def dict(self):
        return {
            'Total suspended MTD': self._total_suspended,
            'Total triggered MTD': self._total_triggered,
            'Total executed MTD': self._total_executed,
            'Total attack interrupted': self._total_attack_interrupted,
            'Switch MTD interval at': self._switch_mtd_interval_at,
            'Switch MTD strategy at': self._switch_mtd_strategy_at
        }

    def append_total_attack_interrupted(self):
        self._total_attack_interrupted += 1

    def append_total_suspended(self):
        self._total_suspended += 1

    def append_total_triggered(self):
        self._total_triggered += 1

    def get_record(self):
        return self._mtd_operation_record
