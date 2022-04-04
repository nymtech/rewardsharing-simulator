import numpy as np
from Input_Functions_econ import Input_Functions
from Network_econ import Network


# This class contains the overall model with variables for user demand, node operational costs, pledging, delegation,
# rewards, vesting, circulating supply, etc.
# The class sets an initial state based on Config and then updates the variables (state) interval-by-interval,
# taking into account the previous state and external environment inputs (user demand, node costs, etc.)
class Econ_Results:
    def __init__(self, config):

        self.config = config  # contains all configuration (input) variables
        self.input_functions = Input_Functions(self.config)  # contains library of pre-set functions for some inputs

        ############
        # Set simulation inputs for user demand, token value, node processing capacity, and create Network object
        ############

        # demand of bandwidth (in nr of packets per month)
        self.bw_demand = self.input_functions.get_function(self.config.type_bw_growth)

        # conversion rate token to dollar (and vice-versa). Currently given by pre-set functions
        # we can add extensions to make the token exchange rate dependent on system variables in some clever way
        self.dollar_per_token = self.input_functions.get_function(self.config.type_token_growth)
        self.token_per_dollar = np.reciprocal(self.dollar_per_token)

        # capacity of mixes over time (in packets per second)
        self.cpus_per_mix = self.input_functions.get_function(self.config.type_cpu_growth)
        self.cpu_capacity = self.input_functions.get_function(self.config.type_capacity_growth)

        # create the network object with a number of mix nodes per interval determined by demand and configuration
        self.network = Network(self.config, self.bw_demand, self.cpus_per_mix, self.cpu_capacity)

        ############
        # set variables for the costs of network operations
        ############

        # flat operational cost for mix nodes, based on preset functions for cpu cost and nr of cpus per mix
        self.cost_cpu_month_dollar = self.input_functions.get_function(self.config.type_cpu_cost_growth)
        self.cost_mix_flat_month_dollar = np.multiply(self.cost_cpu_month_dollar, self.cpus_per_mix)
        self.cost_mix_flat_month_token = np.multiply(self.cost_mix_flat_month_dollar, self.token_per_dollar)
        # bandwidth operational cost for mix nodes actively routing traffic packets in the mixnet
        self.cost_packet_bw_dollar = self.input_functions.get_function(self.config.type_packet_bw_cost_growth)
        self.cost_layer_bw_month_dollar = np.multiply(self.cost_packet_bw_dollar, self.bw_demand)
        self.cost_active_mix_bw_month_dollar = np.divide(self.cost_layer_bw_month_dollar, self.network.mixnet_width)
        self.cost_active_mix_bw_month_token = np.multiply(self.cost_active_mix_bw_month_dollar, self.token_per_dollar)

        ############
        # set initial state for token variables ; then each variable evolves depending on past/present inputs
        ############

        # reserve (pool) of token to be emitted as node rewards over time
        self.mixmining_pool = [self.config.mixmining_pool_initial] * self.config.num_intervals
        # amount of circulating (liquid) tokens
        self.circulating_tokens = [self.config.liquid_tokens_initial] * self.config.num_intervals
        # amount of tokens locked up with a vesting schedule
        self.unvested_tokens = [self.config.unvested_tokens_initial] * self.config.num_intervals
        # maximum stake that could potentially be delegated, needed to compute stake saturation values per node
        self.max_delegatable_stake = [self.config.beta * (self.config.total_token - self.config.mixmining_pool_initial)] * self.config.num_intervals
        # saturation level per mix operator divides available stake share by k
        self.stake_saturation_mix = np.divide(self.max_delegatable_stake, self.network.k)
        # amount of pledged stake to the whole set of nodes
        self.pledged_stake = np.multiply(self.max_delegatable_stake, self.config.frac_token_pledged)
        # amount of delegated stake to the whole set of nodes
        self.delegated_stake = np.multiply(self.max_delegatable_stake, self.config.frac_token_delegated)

        # Price per packet in dollar and token, over the intervals (currently set to constant)
        self.pp_dollar = self.input_functions.get_function(self.config.type_pp_growth)
        self.pp_token = np.multiply(self.pp_dollar, self.token_per_dollar)  # convert price to token

        # rewards emitted from the mixmining pool per interval
        self.mixmining_emitted = [self.config.mixmining_pool_initial * self.config.emission_rate] * self.config.num_intervals

        # rewards from bandwidth fees, and the amount allocated to each category of operator (mix nodes and gateways)
        self.bw_income = np.multiply(self.pp_token, self.bw_demand)  # total income from bw in token
        self.share_income_bw_mix = np.multiply(self.bw_income, self.config.bw_to_mix)
        self.share_income_bw_gw = np.multiply(self.bw_income, self.config.bw_to_gw)

        # global income aggregates mixmining rewards + bw fees for each category of operators
        self.income_global_mix = np.add(self.mixmining_emitted, self.share_income_bw_mix)
        self.income_global = np.add(self.income_global_mix, self.share_income_bw_gw)

        # output: reward distribution variables
        self.rewards_distributed = [0] * self.config.num_intervals  # aggregate rewards distributed to all operators
        self.rewards_distributed_mix = [0] * self.config.num_intervals  # rewards distributed to all mix operators
        self.rewards_unclaimed = [0] * self.config.num_intervals  # rewards not distributed that go back to pool

        ############
        # once initial state is set, update the state on an interval-by-interval basis
        ############

        for month in range(self.config.num_intervals):
            self.compute_next_state(month)

    ################
    # function updates all the global variables for the current month
    # order of calling functions is important! don't randomly mess with ordering
    def compute_next_state(self, month):

        print("processing month", month, "/", self.config.num_intervals)
        self.update_vesting_staking(month)  # update vesting, circulating supply and stake saturation point per node
        # update functions for token price and cost of bw can be uncommented. Current versions are placeholders.
        # self.update_token_price(month)  # update token price (currently a placeholder)
        # self.update_pp(month)  # update price per packet (affects income from bw fees). Baseline is constant value.
        self.update_lists_nodes(month)  # updates the list of all nodes with their individual pledge and delegation
        self.update_costs(month)  # updates the node operational costs in token (must come after update_token_price)
        self.update_mixmining_pool_and_available_rewards(month)  # updates the mixmining pool, rewards, bw income
        self.assign_rewards(month)  # updates the potential and actual rewards per node (dep. pledge/stake)

        # for each node distribute the rewards among individual operators and their delegates
        for mix in self.network.list_mix[month]:
            self.mix_node_rewards_distribute_profits(mix)

    ####################################
    # updates the unvested and circulating supplies as well as the stake saturation point per mix node
    def update_vesting_staking(self, month):

        # for month == 0 the initialized vectors already contain the right values
        if month > 0:
            # check if tokens are vesting on the current month
            if self.unvested_tokens[month - 1] > 0 and month % self.config.vesting_interval == 0:
                vesting = self.config.unvested_tokens_initial * self.config.vesting_interval / self.config.vesting_period
            else:
                vesting = 0

            # update values for unvested and circulating token
            self.unvested_tokens[month] = self.unvested_tokens[month-1] - vesting
            self.circulating_tokens[month] = self.circulating_tokens[month-1] + vesting + \
                                             self.mixmining_emitted[month-1] - self.rewards_unclaimed[month-1]

            # maximum available stake and saturation point
            self.max_delegatable_stake[month] = self.config.beta * (self.config.total_token - self.mixmining_pool[month-1])
            self.stake_saturation_mix[month] = self.max_delegatable_stake[month] / self.network.k[month]

    ####################################
    # updates the conversion rate between token and dollar
    # if the function is preset and independent of system variables, then this function does nothing
    # ready to be extended with functions that evolve based on any combination of variable values of the past state
    def update_token_price(self, month):

        # types of token price functions that are preset and independent of system state
        preset_functions = ['TOK_CONSTANT_50CENT', 'TOK_CONSTANT_100CENT', 'TOK_LINEAR_GROWTH_2CENT',
                            'TOK_EXP_GROWTH_3%_STEADY', 'TOK_EXP_GROWTH_10%_HALVES_12M', 'TOK_EXP_CAPPED_10%_HALVES_3x']

        if self.config.type_token_growth in preset_functions:
            pass  # default initial vector self.dollar_per_token already contains the right values
        # else: here we can introduce token price update functions that are dependent on the past state [month - 1]

        self.token_per_dollar[month] = 1 / self.dollar_per_token[month]

    ####################################
    # updates the price of an anonymous packet
    # if the function is preset and independent of system variables, then this function does nothing
    # ready to be extended with functions that evolve based on any combination of variable values of the past state
    def update_pp(self, month):

        # types of packet price functions that are preset and independent of other system variables
        preset_functions = ['PP_CONSTANT', 'PP_EXP_DECAY_1%']

        if self.config.type_pp_growth in preset_functions:
            pass  # default initial vector self.pp_dollar already contains the right values
        # else: here we can introduce updates to pp_dollar[month] that are dependent on the past system state [month -1]

        self.pp_token[month] = self.pp_dollar[month] * self.token_per_dollar[month]

    ###############
    # updates the list of mix nodes in the network object for the current month
    # network.create_list_mixes() function does the actual job (assign to each node a pledge and delegated stake)
    def update_lists_nodes(self, month):

        # create the lists of mix nodes for the new interval
        self.network.create_list_mixes(month, self.cost_mix_flat_month_token[month], self.stake_saturation_mix[month],
                                       self.pledged_stake[month], self.delegated_stake[month])

    ####################################
    # updates the cost in token of running a node, considering updated token_per_dollar value
    def update_costs(self, month):

        # config.cost_mix_dummy is a lower bound on bw costs (to account for dummy loops when low/no traffic)
        bw_cost = max(self.config.cost_mix_dummy, self.cost_active_mix_bw_month_token[month])

        # update cost per mix by adding to the flat cost (initialized) the variable cost (dependent on activity)
        for mix in self.network.list_mix[month]:
            mix.node_cost += mix.activity_percent * bw_cost

    ####################################
    # updates values for mixmining pool, emitted mixmining rewards and income from fees
    # updates variables keeping track of aggregated network income
    def update_mixmining_pool_and_available_rewards(self, month):

        # update the mixmining pool amount and the emitted mixmining rewards in the current month
        if month > 0:
            # current mixmining pool = previous pool minus previous emitted rewards plus returned (unclaimed) rewards
            self.mixmining_pool[month] = self.mixmining_pool[month - 1] - self.mixmining_emitted[month - 1] + \
                                         self.rewards_unclaimed[month - 1]
            # the newly emitted rewards are a percentage of the current (updated) mixmining pool
            self.mixmining_emitted[month] = self.mixmining_pool[month] * self.config.emission_rate

        # compute the share of bandwidth income to be distributed to each category of operator
        self.bw_income[month] = self.bw_demand[month] * self.pp_token[month]
        self.share_income_bw_mix[month] = self.bw_income[month] * self.config.bw_to_mix
        self.share_income_bw_gw[month] = self.bw_income[month] * self.config.bw_to_gw

        # compute the global income for each category of operator (sum of previous two values)
        self.income_global_mix[month] = self.mixmining_emitted[month] + self.share_income_bw_mix[month]
        self.income_global[month] = self.income_global_mix[month] + self.share_income_bw_gw[month]

    ####################################
    # takes the pot of rewards for mix nodes and computes the R_i (white paper formula) for each individual mix
    # updates global variables on rewards distributed and unclaimed (that are put back in mixmining pool)
    def assign_rewards(self, month):

        active_nodes = self.config.mixnet_layers * self.network.mixnet_width[month]
        idle_nodes = self.network.k[month] - active_nodes
        factor = self.config.factor_work_active  # active node's omega is "factor" times higher than idle node's omega
        work_active = factor / (factor * self.network.k[month] - (factor - 1) * idle_nodes)
        work_idle = 1 / (factor * self.network.k[month] - (factor - 1) * idle_nodes)

        # compute rewards distributed to each of the mixes (depending on their pledge, stake, performance)
        for mix in self.network.list_mix[month]:
            # received rewards (formula rewards paper) for the epochs when the node was active
            mix.received_rewards = mix.activity_percent * mix.performance * self.income_global_mix[month] * \
                                   mix.sigma_node * self.network.k[month] * (work_active + self.config.alpha *
                                                                             mix.lambda_node) / (1 + self.config.alpha)
            # received rewards (formula rewards paper) for the epochs when the node was in reserve
            mix.received_rewards += mix.reserve_percent * mix.performance * self.income_global_mix[month] * \
                                    mix.sigma_node * self.network.k[month] * (work_idle + self.config.alpha *
                                                                              mix.lambda_node) / (1 + self.config.alpha)
            # mix receives nothing for (1 - mix.activity_percent - mix.reserve_percent) where it's not selected

            # set variables for distributed and unclaimed (diff between potential and actual) rewards
            self.rewards_distributed_mix[month] += mix.received_rewards

        # aggregate of rewards distributed to nodes and gws. Note these are not profits: costs NOT YET subtracted
        self.rewards_distributed[month] = self.rewards_distributed_mix[month] + self.share_income_bw_gw[month]
        # amount of rewards unclaimed and returned to the mixmining pool
        self.rewards_unclaimed[month] = self.income_global[month] - self.rewards_distributed[month]

    ###################################
    # Given a mix node, this function splits the profit between the operator and the delegates.
    # it sets the variables operator_profit and delegate_profit for each of the nodes
    def mix_node_rewards_distribute_profits(self, mix):

        # FIRST subtract the operational cost from the rewards awarded to the node (to compute the profit)
        profit = mix.received_rewards - mix.node_cost  # profit is negative if the costs are higher than the rewards

        # SECOND distribute profit among operator and delegates (following white paper formulas)
        # If there is a (positive) profit, split it with the formulas
        if profit > 0:
            mix.operator_profit = (self.config.node_profit_margin + (1 - self.config.node_profit_margin) * (
                    mix.pledge / (mix.pledge + mix.delegated))) * profit
            mix.delegate_profit = (1 - self.config.node_profit_margin) * (mix.delegated / (
                    mix.pledge + mix.delegated)) * profit
        else:  # if there is no profit, delegates get nothing and the loss is on the operator profit (who paid costs)
            mix.operator_profit = profit
            mix.delegate_profit = 0

    # This function returns a dictionary where dict_distr[month] is a vector with the values for parameter 'par'
    # for the list of existing nodes (ordered by node index)
    # the result can be used for boxplots that show the distribution of a variable's values for a set of nodes
    def get_dictionary_distribution(self, par):

        dict_distr = {}
        for month in range(self.config.num_intervals):
            dict_distr[month] = []
            for node in self.network.list_mix[month]:
                next_val = self.get_node_value(node, par)
                dict_distr[month].append(next_val)

        return dict_distr

    # returns the parameter value for a node
    def get_node_value(self, node, par):

        if par == 'serial':
            res = node.serial
        elif par == 'sat_level':
            res = node.sat_level
        elif par == 'pledge':
            res = node.pledge
        elif par == 'delegated':
            res = node.delegated
        elif par == 'total_stake':
            res = node.delegated + node.pledge
        elif par == 'node_cost':
            res = node.node_cost
        elif par == 'received_rewards':
            res = node.received_rewards
        elif par == 'operator_profit':
            res = node.operator_profit
        elif par == 'delegate_profit':
            if node.delegated > 0:
                res = node.delegate_profit
            else:
                res = None
        elif par == 'lambda':
            res = node.lambda_node
        elif par == 'sigma':
            res = node.sigma_node
        elif par == 'saturation_percent':
            res = (node.pledge + node.delegated) / node.stake_saturation
        elif par == 'pledge_saturation_percent':
            res = node.pledge / node.stake_saturation
        elif par == 'activity_percent':
            res = node.activity_percent
        elif par == 'reserve_percent':
            res = node.reserve_percent
        elif par == 'ROS_operator':  # takes operational costs into account
            res = node.operator_profit / (node.pledge + node.node_cost)
        elif par == 'ROS_delegator':
            if node.delegated > 0:
                res = node.delegate_profit / node.delegated
            else:
                res = None
        else:
            res = None
            print("ISSUE: bad parameter type passed to get_node_value in Econ_results")
            exit("ERROR: bad parameter type !")
        return res

    # stake is the amount of token available to the participant
    # function returns a dictionary with 2 scenarios: pledge or delegate to a mix node
    # for each of the two scenarios, sample nodes representing the rewards that the stakeholder would
    # obtain for pledging/delegating the available stake on a node
    def sample_annualized_rewards_no_compound_vs_saturation(self, stake):

        # rewards dictionary contains a dictionary for each of options: pledge/delegate on a mix
        rewards = {'pledge-mix': {}, 'sat-pledge-mix': {}, 'delegate-mix': {}, 'sat-delegate-mix': {}}
        # the dictionary also records the saturation level of the node (reputation level) for the sampled nodes

        # rewards['delegate-mix'][month] contains a list of sample rewards based on the ROS of mixes in the simulation
        for month in range(self.config.num_intervals):
            rewards['pledge-mix'][month] = []
            rewards['sat-pledge-mix'][month] = []
            rewards['delegate-mix'][month] = []
            rewards['sat-delegate-mix'][month] = []

            for mix in self.network.list_mix[month]:
                # select nodes whose pledge value is around staking budget plus/minus 20%
                if 0.8 * stake <= mix.pledge <= 1.2 * stake:
                    ros_mix_operator = self.get_node_value(mix, 'ROS_operator')
                    rewards['pledge-mix'][month].append(stake * 12 * ros_mix_operator)
                    stake_saturation = self.get_node_value(mix, 'saturation_percent')
                    rewards['sat-pledge-mix'][month].append(stake_saturation)

                # delegation only requires more delegated stake than investment
                ros_mix_delegate = self.get_node_value(mix, 'ROS_delegator')
                if (ros_mix_delegate is not None) and (stake <= mix.delegated):
                    rewards['delegate-mix'][month].append(stake * 12 * ros_mix_delegate)
                    stake_saturation = self.get_node_value(mix, 'saturation_percent')
                    rewards['sat-delegate-mix'][month].append(stake_saturation)

        return rewards

