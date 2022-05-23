
# class contains the variables and functions to define a stakeholder and compute the rewards
class Stakeholder:
    def __init__(self, type_holder, config):
        self.type_holder = type_holder  # type of stakeholder: 'TESTNET', 'OPTION_1', 'OPTION_2', 'WHALE', 'VALIDATOR'
        self.config = config
        # the variables below are stake distribution priors determined by type of stakeholder
        self.liquid_stake = [0] * config.num_intervals  # liquid stake owned by stakeholder (prior)
        self.unvested_stake = [0] * config.num_intervals  # unvested stake owned by stakeholder (prior)
        self.total_stake = [0] * config.num_intervals  # total (liquid+unvested) stake owned by stakeholder (prior)
        self.effective_stake = [0] * config.num_intervals  # effective holdings to stake (1% of unvested + 100% of liquid)
        # the variables below are computed based on simulation APYs
        self.rewards = [0] * config.num_intervals  # received staking rewards per month
        self.rewards_cumulative = [0] * config.num_intervals  # cumulative received rewards
        self.effective_compounded_stake = [0] * config.num_intervals  # effective stake with compounding rewards
        self.wealth_compounded_stake = [0] * config.num_intervals  # total stake with compounding rewards

        self.create_participant()

    def compute_rewards(self, median_ROS):

        # rewards of first interval
        self.rewards[0] = median_ROS[0] * self.effective_compounded_stake[0]
        self.rewards_cumulative[0] = self.rewards[0]  # initialize cumulative version
        # from second month, compound wealth and staking
        for month in range(1, self.config.num_intervals):
            self.wealth_compounded_stake[month] += self.rewards_cumulative[month-1]
            self.effective_compounded_stake[month] += self.rewards_cumulative[month-1]
            self.rewards[month] = median_ROS[month] * self.effective_compounded_stake[month]
            self.rewards_cumulative[month] = self.rewards_cumulative[month-1] + self.rewards[month]

    def create_participant(self):

        if self.type_holder == 'TESTNET':
            self.create_liquid_participant(1250)
        elif self.type_holder == 'OPTION_1':
            self.create_liquid_participant(1000)
        elif self.type_holder == 'OPTION_2':
            self.create_liquid_participant(4000)
        elif self.type_holder == 'VALIDATOR_400k':
            self.create_locked_participant(400 * 10**3)
        elif self.type_holder == 'VALIDATOR_200k':
            self.create_locked_participant(200 * 10**3)
        elif self.type_holder == 'VALIDATOR_100k':
            self.create_locked_participant(100 * 10**3)
        elif self.type_holder == 'WHALE_1M':
            self.create_locked_participant(10**6)
        elif self.type_holder == 'WHALE_10M':
            self.create_locked_participant(10 * 10**6)
        elif self.type_holder == 'WHALE_80M':
            self.create_locked_participant(80 * 10 ** 6)
        else:
            exit("error: type of stakeholder does not exist")

        for month in range(self.config.num_intervals):
            self.total_stake[month] = self.liquid_stake[month] + self.unvested_stake[month]

            if self.unvested_stake[month] < self.config.cap_staking_unvested:  # amount of locked token below the cap
                self.effective_stake[month] = self.liquid_stake[month] + self.unvested_stake[month]
            else:  # account has more unlocked token than the cap
                self.effective_stake[month] = self.liquid_stake[month] + self.config.cap_staking_unvested + \
                                              self.config.frac_staking_unvested * (
                                                      self.unvested_stake[month] - self.config.cap_staking_unvested)

            # initialize compounded versions (which are later updated)
            self.wealth_compounded_stake[month] = self.total_stake[month]
            self.effective_compounded_stake[month] = self.effective_stake[month]

    # sets stake for a participant that either has liquid tokens or has an amount of locked tokens under the 100k cap
    def create_liquid_participant(self, purchase):
        for month in range(self.config.num_intervals):
            self.liquid_stake[month] = purchase

    # sets stake for a whale with a purchase amount of NYM
    def create_locked_participant(self, purchase):

        for month in range(self.config.num_intervals):
            batches_vested = min(8, month // 3)  # zero liquidity until month 3, variable maxes at 8 batches
            batches_unvested = 8 - batches_vested  # decreases from 8 to zero (unvested batches)
            self.liquid_stake[month] = purchase * batches_vested / 8
            self.unvested_stake[month] = purchase * batches_unvested / 8

