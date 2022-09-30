import logging

# parameters for capacity of application layer and network layer

MTD_INTERVAL = 30


class MTDSchedule:
    def __init__(self, network, mtd_strategy_schedule):
        self.mtd_interval_schedule = MTD_INTERVAL
        self.mtd_strategy_schedule = mtd_strategy_schedule
        self.timestamps = None
        self.compromised_ratios = None
        self.network = network

    def adapt_schedule_by_time(self, env):
        now = env.now
        if (self.timestamps[0] <= now < self.timestamps[1]) and (self.mtd_interval_schedule > 30):
            self.mtd_interval_schedule /= 2
            logging.info('Shorten the time interval to %.1f at %.1fs!'
                         % (self.mtd_interval_schedule, now))
            self.network.get_mtd_stats().append_mtd_interval_record(now, self.mtd_interval_schedule)
        elif (now >= self.timestamps[1]) and (15 < self.mtd_interval_schedule <= 30):
            self.mtd_interval_schedule /= 2
            logging.info('Shorten the time interval to %.1f at %.1fs!'
                         % (self.mtd_interval_schedule, now))
            self.network.get_mtd_stats().append_mtd_interval_record(now, self.mtd_interval_schedule)
        return self.mtd_interval_schedule

    # def adapt_schedule_by_compromised_ratio(self, env, compromised_ratio):
    #     now = env.now
    #     if (self.compromised_ratios[0] <= compromised_ratio < self.compromised_ratios[1]) and \
    #             len(self.mtd_strategy_schedule) < 4:
    #         logging.info('Current compromised ratio is %.2f, switch to shuffle mtd strategy schedule at %.1fs!'
    #                      % (compromised_ratio, now))
    #         self.mtd_strategy_schedule = MTD_SHUFFLE
    #         self.network.get_mtd_stats().append_mtd_strategy_record(now, 'shuffle')
    #     elif compromised_ratio >= self.compromised_ratios[1] and \
    #             len(self.mtd_strategy_schedule) < 5:
    #         logging.info('current compromised ratio is %.2f, switch to hybrid mtd strategy schedule at %.1fs!'
    #                      % (compromised_ratio, now))
    #         self.mtd_strategy_schedule = MTD_HYBRID
    #         self.network.get_mtd_stats().append_mtd_strategy_record(now, 'hybrid')
    #     return self.mtd_strategy_schedule

    def set_timestamps(self, timestamps: list):
        self.timestamps = timestamps

    def set_compromised_ratios(self, compromised_ratios):
        self.compromised_ratios = compromised_ratios

    def set_mtd_interval_schedule(self, mtd_interval_schedule):
        self.mtd_interval_schedule = mtd_interval_schedule

    def set_mtd_strategy_schedule(self, mtd_strategy_schedule):
        self.mtd_strategy_schedule = mtd_strategy_schedule

    def extend_mtd_strategy_schedule(self, mtd_strategies: list):
        self.mtd_strategy_schedule.extend(mtd_strategies)

    def get_mtd_interval_schedule(self):
        return self.mtd_interval_schedule

    def get_mtd_strategy_schedule(self):
        return self.mtd_strategy_schedule

