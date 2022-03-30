
# Contains a library of preset functions that can be used to model: bandwidth demand, token-dollar exchange rate,
# price per packet for users, cpu processing capacity (sphinx messages / second), number of cpus per mix,
# cost cpu (flat per month), and cost bandwidth for node operators (in packets per second,
# which may need translation from GB which is obtained multiplying by average packet length)
class Input_Functions:

    def __init__(self, config):
        self.num_intervals = config.num_intervals
        self.config = config

    # main function that is called by external classes to obtain functions that describe different variables
    def get_function(self, f_type):

        # Used for demand growth function (zero demand)
        if f_type == 'BW_ZERO':
            y = [0] * self.num_intervals  # overrides self.config.initial_bandwidth value

        # Used for demand growth of bandwidth (linear growth)
        elif f_type == 'BW_LINEAR_GROWTH_10kps':
            a = self.config.initial_bandwidth * 3600 * 24 * 30  # initial packets/second value given in config
            b = 10000 * 3600 * 24 * 30  # 10k extra packets/second per month
            y = self.get_linear_function(a, b)

        # Used for demand growth of bandwidth (exponential growth)
        elif f_type == 'BW_EXP_GROWTH_6%_STEADY':
            a = self.config.initial_bandwidth * 3600 * 24 * 30  # initial packets/second value given in config
            v = [1.06] * self.num_intervals
            y = self.get_exponential_function(a, v)

        # Used for demand growth of bandwidth (exponential growth)
        elif f_type == 'BW_EXP_GROWTH_10%_STEADY':
            a = self.config.initial_bandwidth * 3600 * 24 * 30  # initial packets/second value given in config
            v = [1.1] * self.num_intervals
            y = self.get_exponential_function(a, v)

        # Used for demand growth of bandwidth
        elif f_type == 'BW_EXP_GROWTH_10%_HALVES_6M':
            a = self.config.initial_bandwidth * 3600 * 24 * 30  # initial packets/second value given in config
            initial_growth = 0.1
            reduction_factor = 0.5  # halves the growth
            reduction_period = 6  # the reduction of growth rate happens every 6 intervals
            y = self.get_exp_periodic_reduction(a, initial_growth, reduction_period, reduction_factor)

        # Used for demand growth of bandwidth
        elif f_type == 'BW_EXP_GROWTH_10%_HALVES_12M':
            a = self.config.initial_bandwidth * 3600 * 24 * 30  # initial packets/second value given in config
            initial_growth = 0.1
            reduction_factor = 0.5  # halves the growth
            reduction_period = 12  # the reduction of growth rate happens every 12 intervals
            y = self.get_exp_periodic_reduction(a, initial_growth, reduction_period, reduction_factor)

        # Used for demand growth of bandwidth
        elif f_type == 'BW_EXP_GROWTH_10%_DROP1/4_6M':
            a = self.config.initial_bandwidth * 3600 * 24 * 30  # initial packets/second value given in config
            initial_growth = 0.1
            reduction_factor = 0.75  # cuts growth rate by 25%
            reduction_period = 6  # the reduction of growth rate happens every 6 intervals
            y = self.get_exp_periodic_reduction(a, initial_growth, reduction_period, reduction_factor)

        # Used for demand growth of bandwidth
        # this function starts at a value a and grows at 10% each interval
        # until it hits 10x growth (10*a), when it starts growing at 5% (half rate)
        # when it hits 100 growth (10*10*a), it grows at 2.5% (rate halves again)
        # each time it grows 10x, growth rate slows down by half
        elif f_type == 'BW_EXP_CAPPED_10%_HALVES_10x':
            a = self.config.initial_bandwidth * 3600 * 24 * 30  # initial packets/second value given in config
            initial_growth = 0.1
            reduction_factor = 0.5  # halves the growth
            order_mag_cap = 10  # order of magnitude at which growth slows down
            y = self.get_exp_cap_reduction_function(a, order_mag_cap, initial_growth, reduction_factor)

        # Used for demand growth of bandwidth
        # this function starts at a value a and grows at 10% each interval
        # until it hits 4x growth (4*a), when it starts growing at 5% (half rate)
        # when it hits 16x growth (4*4*a), it grows at 2.5% (rate halves again)
        # each time it grows 4x, growth rate slows down by half
        elif f_type == 'BW_EXP_CAPPED_10%_HALVES_4x':
            a = self.config.initial_bandwidth * 3600 * 24 * 30  # initial packets/second value given in config
            initial_growth = 0.1
            reduction_factor = 0.5  # halves the growth
            order_mag_cap = 4  # order of magnitude at which growth slows down
            y = self.get_exp_cap_reduction_function(a, order_mag_cap, initial_growth, reduction_factor)

        # Used for demand growth of bandwidth
        # this function starts at a value a and grows at 10% each interval
        # until it hits 4x growth (4*a), when it starts growing at 66.7% rate (two thirds of previous rate)
        # each time it grows 4x, growth rate is cut by one third
        elif f_type == 'BW_EXP_CAPPED_10%_DROP1/3_4x':
            a = self.config.initial_bandwidth * 3600 * 24 * 30  # initial packets/second value given in config
            initial_growth = 0.1
            reduction_factor = 0.667  # growth is 2/3 of what it was in previous stretch
            order_mag_cap = 4  # order of magnitude at which growth slows down
            y = self.get_exp_cap_reduction_function(a, order_mag_cap, initial_growth, reduction_factor)

        ############################
        ############################
        # Used for token exchange rate (constant at initial config value)
        elif f_type == 'TOK_CONSTANT':
            a = self.config.token_launch_price  # initial price config
            y = [a] * self.num_intervals

        # Used for token exchange rate (constant at $1)
        elif f_type == 'TOK_CONSTANT_100CENT':
            a = 1  # 1 dollar per token fixed rate forever
            y = [a] * self.num_intervals

        # Used for token exchange rate (linear growth)
        elif f_type == 'TOK_LINEAR_GROWTH_2CENT':
            a = self.config.token_launch_price  # initial price config
            b = 0.02  # change to 0.0X for X cent increase per month
            y = self.get_linear_function(a, b)

        # Used for token exchange rate (exponential growth)
        elif f_type == 'TOK_EXP_GROWTH_3%_STEADY':
            a = self.config.token_launch_price  # initial price config
            v = [1.03] * self.num_intervals  # 3% increase per month
            y = self.get_exponential_function(a, v)

        # Used for token exchange rate
        elif f_type == 'TOK_EXP_GROWTH_10%_HALVES_12M':
            a = self.config.token_launch_price  # initial price config
            initial_growth = 0.1  # starts by growing 10% per interval
            reduction_factor = 0.5  # reduces growth factor by half every reduction period
            reduction_period = 12  # the reduction of growth rate happens every 12 intervals
            y = self.get_exp_periodic_reduction(a, initial_growth, reduction_period, reduction_factor)

        # Used for token exchange rate
        # this function starts at a value a and grows at 10% each interval
        # until it hits 3x growth (3*a), when it starts growing at 5% (half rate)
        # when it hits 9x growth (3*3*a), it grows at 2.5% (rate halves again)
        # each time it grows 3x, growth rate is cut by half
        elif f_type == 'TOK_EXP_CAPPED_10%_HALVES_3x':
            a = self.config.token_launch_price  # initial price config
            initial_growth = 0.1
            reduction_factor = 0.5  # reduces growth factor by half every time
            order_mag_cap = 3  # order of magnitude at which growth slows down
            y = self.get_exp_cap_reduction_function(a, order_mag_cap, initial_growth, reduction_factor)

        ############################
        ############################
        # Used for price per packet in dollar (constant)
        elif f_type == 'PP_CONSTANT':
            a = self.config.price_packet_initial_dollar  # initial price config
            y = [a] * self.num_intervals

        # Used for price per packet in dollar (exponential decay)
        elif f_type == 'PP_EXP_DECAY_1%':
            a = self.config.price_packet_initial_dollar  # start at config price
            b = 0.99  # price per packet decays by 1% each month
            v = [b] * self.num_intervals
            y = self.get_exponential_function(a, v)

        ############################
        ############################
        # Used for CPU processing of packets per second (constant)
        elif f_type == 'CPU_CONSTANT_PPS':
            a = self.config.cpu_capacity_initial
            y = [a] * self.num_intervals

        # Used for CPU processing of packets per second (linearly increasing capacity)
        elif f_type == 'CPU_LINEAR_100PPS':
            a = self.config.cpu_capacity_initial
            b = 100  # every month it a cpu process 100 more packets per second
            y = self.get_linear_function(a, b)

        # Used for CPU processing of packets per second (exponentially increasing capacity)
        elif f_type == 'CPU_EXP_3%_STEADY':
            a = self.config.cpu_capacity_initial
            b = 1.03  # each interval (month) it gets 3% faster
            v = [b] * self.num_intervals
            y = self.get_exponential_function(a, v)

        # Used for CPU processing of packets per second (exponentially increasing capacity)
        elif f_type == 'CPU_EXP_1%_STEADY':
            a = self.config.cpu_capacity_initial
            b = 1.01  # each interval (month) it gets 1% faster
            v = [b] * self.num_intervals
            y = self.get_exponential_function(a, v)

        ############################
        ############################
        # Used for number of CPUs per node (constant)
        elif f_type == 'N_CPU_CONSTANT':
            y = [self.config.cpus_per_mix_initial] * self.num_intervals

        # Used for number of CPUs per node (linear increase)
        elif f_type == 'N_CPU_LINEAR_1CPU':
            a = self.config.cpus_per_mix_initial
            b = 1  # every month mixes add one cpu
            y = self.get_linear_function(a, b)

        # Used for number of CPUs per node (periodic doubling)
        elif f_type == 'N_CPU_EXP_DOUBLE_36M':
            a = self.config.cpus_per_mix_initial
            v = [1] * self.num_intervals
            for i in range(self.num_intervals):
                if (i % 36) == 0:
                    v[i] = 2  # nr of cpus doubles every 36 months (3 years)
            y = self.get_exponential_function(a, v)

        ############################
        ############################
        # Used for evolution CPU cost (constant)
        elif f_type == 'COST_CPU_CONSTANT':
            y = [self.config.monthly_cost_cpu_initial_dollar] * self.num_intervals

        # Used for evolution CPU cost: 2% cheaper each month
        elif f_type == 'COST_CPU_DECLINE_2%':
            a = self.config.monthly_cost_cpu_initial_dollar  # start at config price
            v = [0.98] * self.num_intervals  # price per packet decay by 2% each month
            y = self.get_exponential_function(a, v)

        # Used for evolution CPU cost: 20% cheaper each year
        elif f_type == 'COST_CPU_DOWN20%_12M':
            a = self.config.monthly_cost_cpu_initial_dollar  # start at config price
            v = [1] * self.num_intervals
            reduction_period = 12  # the reduction of growth rate happens every 12 intervals
            for i in range(1, self.num_intervals):
                if (i % reduction_period) == 0:
                    v[i] = 0.8
            y = self.get_exponential_function(a, v)

        ############################
        ############################
        # Used for evolution bandwidth cost (constant)
        elif f_type == 'COST_BW_CONSTANT':
            y = [self.config.cost_packet_bw_initial_dollar] * self.num_intervals

        # Used for evolution bandwidth cost: 1% cheaper each month
        elif f_type == 'COST_BW_DECLINE_1%':
            a = self.config.cost_packet_bw_initial_dollar  # start at config price
            v = [0.99] * self.num_intervals  # price per packet decay by 1% each month
            y = self.get_exponential_function(a, v)

        # Used for evolution bandwidth cost: 10% cheaper each year
        elif f_type == 'COST_BW_DOWN10%_12M':
            a = self.config.cost_packet_bw_initial_dollar  # start at config price
            v = [1] * self.num_intervals
            reduction_period = 12  # the reduction of growth rate happens every 12 intervals
            for i in range(1, self.num_intervals):
                if (i % reduction_period) == 0:
                    v[i] = 0.9
            y = self.get_exponential_function(a, v)

        ############################
        ############################
        # unrecognized type of function
        else:
            y = []

        return y

    # returns a linear function y = a + bx  (with b=0 it is a constant function)
    def get_linear_function(self, a, b):
        y = [a]
        for i in range(1, self.num_intervals):
            next_val = max(a + (b * i), 0)
            y.append(next_val)
        return y

    # returns an exponential function: y[i] = v[i] * y[i-1]
    def get_exponential_function(self, a, v):

        y = [a]
        for i in range(1, self.num_intervals):
            next_val = max(y[-1] * v[i], 0)
            y.append(next_val)
        return y

    # returns an exponential function where the growth rate is reduced periodically by a reduction factor
    def get_exp_periodic_reduction(self, a, initial_growth, reduction_period, reduction_factor):

        growth = initial_growth
        v = [1.0 + growth]
        for i in range(1, self.num_intervals):
            if (i % reduction_period) == 0:
                growth = growth * reduction_factor
            v.append(1.0 + growth)
        y = self.get_exponential_function(a, v)
        return y

    # function grows exponentially each round by factor initial_growth until it hits the first cap
    # then grows by reduced factor until second cap, and so on, growing at slower rate over time
    def get_exp_cap_reduction_function(self, a, order_mag_cap, initial_growth, reduction_factor):

        v_caps = [a * order_mag_cap]
        for i in range(20):  # way more than enough caps
            v_caps.append(v_caps[-1] * order_mag_cap)

        y = [a]
        growth = initial_growth
        cap_ind = 0
        cap = v_caps[cap_ind]
        for i in range(1, self.num_intervals):
            next_val = y[-1] * (1.0 + growth)
            y.append(next_val)
            if next_val > cap:
                growth = growth * reduction_factor
                cap_ind += 1
                cap = v_caps[cap_ind]
        return y

