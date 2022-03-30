import math
import random
import numpy as np
from numpy.random import random_sample
from Node_econ import Node


# This class contains the existing mix nodes per interval (main variable: the list_mix dictionary)
# For each interval the class generates a number of nodes per interval, proportionally to demand (with a min bound)
# For each mix node of each interval the class computes its staking (pledge + delegation) and samples its activity level
# The dictionary list_mix also stores the rewards received per interval by each node operator and its delegates
class Network:
    def __init__(self, config, bw_demand, cpus_per_mix, cpu_capacity):

        self.config = config  # contains all the input variables
        self.bw_demand = bw_demand  # vector with the aggregate nr of sphinx packets per month from users

        # translation of bandwidth demand to nr mixes wanted to cover that demand, considering candidate excess factors
        self.mix_capacity = np.multiply(cpu_capacity, cpus_per_mix)  # max nr of packets per second per mix over time
        self.mix_avg_load = np.divide(self.mix_capacity, self.config.peak_factor)  # average load relative to peak
        self.bw_demand_avg_second = np.divide(self.bw_demand, (3600 * 24 * 30))  # conversion of bw_demand to seconds
        self.mixnet_width = self.set_mixnet_width()  # compute mixnet width per interval considering bw_demand
        self.k = self.set_k_mixes()  # compute nr of rewarded mixes per interval considering bw_demand and configuration
        self.num_mixes = []  # total number of registered mix nodes, assumed to be in excess of the equilibrium value k
        for i in range(self.config.num_intervals):
            self.num_mixes.append(int(round(self.k[i] * self.config.excess_candidate_factor)))

        # dictionaries containing values for all nodes of all intervals
        self.list_mix = {}  # dictionary mixes, one entry per interval containing list of mix nodes for the interval
        for month in range(self.config.num_intervals):
            self.list_mix[month] = []  # per interval, create list of Nodes existing in that interval

    # Returns a vector with the minimum required mixnet width per interval
    # The result is determined by the average traffic per second and the average throughput of mixes
    # The variable self.config.min_mixnet_width imposes a lower bound on the width
    def set_mixnet_width(self):

        min_width_traffic = np.divide(self.bw_demand_avg_second, self.mix_avg_load)
        width = []
        for i in range(self.config.num_intervals):
            w = max(math.ceil(min_width_traffic[i]), self.config.min_mixnet_width)
            width.append(w)
        return width

    # Returns a vector with the number k of rewarded mix nodes per interval (month)
    # k is a the target equilibrium parameter of the reward algorithm
    # In the implemented function type the result is given by mixnet_width, mixnet_layers and mix_active_rate
    # self.config.nr_min_mixes sets a lower bound on the value of k
    # Additional function types can be added if we want to set the number k of rewarded nodes differently
    def set_k_mixes(self):

        if self.config.type_mixnet_growth == 'MIXNET_LINEAR_GROWTH_WITH_TRAFFIC':
            k = []  # parameter k that determines how many mix nodes are rewarded per interval
            for i in range(self.config.num_intervals):
                mixnet_total = math.ceil((self.mixnet_width[i] * self.config.mixnet_layers) / self.config.mix_active_rate)
                k.append(max(mixnet_total, self.config.nr_min_mixes))
        else:
            k = None  # no other options for now, we could add them if desired

        return k

    # Creates a vector with all the mix nodes and appends them to self.list_mix[month]
    # Sets pledge amounts, delegation amounts and other node variables
    def create_list_mixes(self, month, cost_node_month, stake_saturation, pledged_stake, delegated_stake):

        # compute number of nodes with saturated, minimum and random pledge
        nr_nodes_sat_pledge = int(round(self.config.frac_whale_mix * self.k[month]))  # frac of k! (equilibrium parameter)
        nr_nodes_min_pledge = int(round(self.config.frac_min_pledge_mix * self.num_mixes[month]))  # frac of total !!
        nr_nodes_rand_pledge = self.num_mixes[month] - nr_nodes_sat_pledge - nr_nodes_min_pledge  # nr that has a randomized pledge

        # compute the pledge budget remaining for random pledges, by subtracting from the total budget available:
        # the combined pledges of all saturated nodes, as well as the minimum pledges for all unsaturated nodes
        budget_pledge_remain = pledged_stake - nr_nodes_sat_pledge * stake_saturation - \
                               (nr_nodes_min_pledge + nr_nodes_rand_pledge) * self.config.minimum_pledge_mix
        if budget_pledge_remain < 0:
            print("ISSUE: Not enough pledge to allocate minimum amount to enough MIX nodes !!!")
            print("In Config: increase frac_token_pledged; decrease minimum_pledge_mix; or decrease frac_whale_mix.")
            exit("error: pledge budget insufficient for minimum coverage of all nodes")

        # create nr_nodes_sat_pledge with saturated pledges
        for index in range(nr_nodes_sat_pledge):
            node_serial = index
            pledge = stake_saturation
            node = Node(node_serial, 'SAT', pledge, self.config.node_profit_margin,  self.config.node_performance,
                        cost_node_month, stake_saturation)
            self.list_mix[month].append(node)

        # maximum excess over the minimum pledge to reach saturation
        max_excess = stake_saturation - self.config.minimum_pledge_mix
        # excess_pledge[index] contains the excess (over the minimum) pledge of the nr_nodes_rand_pledge nodes
        excess_pledge = self.compute_excess_pledge_pareto_ish(nr_nodes_rand_pledge, budget_pledge_remain, max_excess)
        # create nr_nodes_rand_pledge nodes with random pledge
        for index in range(nr_nodes_rand_pledge):  # create node and add it to list
            node_serial = index + nr_nodes_sat_pledge
            pledge = self.config.minimum_pledge_mix + excess_pledge[index]
            node = Node(node_serial, 'RND', pledge, self.config.node_profit_margin, self.config.node_performance,
                        cost_node_month, stake_saturation)
            self.list_mix[month].append(node)

        # create nr_nodes_min_pledge nodes with minimum pledge
        for index in range(nr_nodes_min_pledge):  # create node and add it to list
            node_serial = index + nr_nodes_sat_pledge + nr_nodes_rand_pledge
            pledge = self.config.minimum_pledge_mix
            node = Node(node_serial, 'MIN', pledge, self.config.node_profit_margin, self.config.node_performance,
                        cost_node_month, stake_saturation)
            self.list_mix[month].append(node)

        # function randomizes the allocation of delegated stake to unsaturated nodes
        self.allocate_delegated_stake_mixnet(month, stake_saturation, delegated_stake)

        # set the lambda and sigma variables of all mix nodes
        total_stake = stake_saturation * self.k[month]
        self.set_lambda_sigma_mixnet(month, total_stake)

        # Finally, update the activity level (share of workload) of the nodes
        activity_vector, reserve_vector = self.estimate_work_share_mixes(month)
        # set the activity and reserve values in each of the nodes of the list for the interval
        for mix in self.list_mix[month]:
            mix.activity_percent = activity_vector[mix.serial]
            mix.reserve_percent = reserve_vector[mix.serial]

    # returns a vector excess_pledge with nr_nodes_rand_pledge values distributed following a pareto distribution.
    # The values of excess_pledge add up to remaining_pledge and no value is higher than max_excess
    def compute_excess_pledge_pareto_ish(self, nr_nodes_rand_pledge, remaining_pledge, max_excess):

        if nr_nodes_rand_pledge == 0:
            return []
        excess_pledge = [0] * nr_nodes_rand_pledge
        shape = 1.16  # value that fulfills 80-20 distribution rule
        samples = np.random.pareto(shape, nr_nodes_rand_pledge)
        normalized_samples = np.divide(samples, sum(samples))
        # if the maximum value is higher than max, cap and rescale the pledging to 95% of maximum value
        while max(normalized_samples) * remaining_pledge > max_excess:
            for ind in range(nr_nodes_rand_pledge):
                if normalized_samples[ind] * remaining_pledge > max_excess:
                    # cap the highest (over the max) values to 98% of maximum
                    normalized_samples[ind] = 0.98 * max_excess / remaining_pledge
            # renormalize the vector after capping max values to 98% of maximum
            normalized_samples = np.divide(normalized_samples, sum(normalized_samples))

        # set excess_pledge for nr_nodes_rand_pledge and leave at zero for the remaining nr_nodes_min_pledge
        for i in range(nr_nodes_rand_pledge):
            excess_pledge[i] = normalized_samples[i] * remaining_pledge

        return excess_pledge

    # Takes the budget of available stake to delegate and allocates random amounts it to nodes, capped by saturation
    # Allocation is iterative, in order of node index, until the available budget for delegation is exhausted
    # The result changes the node.delegated values for the interval (month)
    # Alternative functions are possible for allocating delegated stake to nodes
    def allocate_delegated_stake_mixnet(self, month, stake_saturation, all_delegated_stake):

        remain_delegated_stake = all_delegated_stake
        while remain_delegated_stake > 0:
            for mix in self.list_mix[month]:
                if mix.pledge + mix.delegated < stake_saturation:  # only delegate to unsaturated nodes
                    # uniform between zero and maxing out on stake
                    sample = random_sample() * (stake_saturation - mix.pledge - mix.delegated)
                    if sample < remain_delegated_stake:
                        mix.delegated += sample
                        remain_delegated_stake -= sample
                    else:  # last one gets remains and following ones get zero delegated
                        mix.delegated += remain_delegated_stake
                        remain_delegated_stake = 0

    # for each node registered in the interval, compute lambda and sigma based on node staking and token supply
    def set_lambda_sigma_mixnet(self, month, total_stake):

        for mix in self.list_mix[month]:
            mix.lambda_node = min(mix.pledge / total_stake, 1 / self.k[month])
            mix.sigma_node = min((mix.pledge + mix.delegated) / total_stake, 1 / self.k[month])

    # given the list of mix nodes in an interval (month), perform per-epoch (per-hour) sampling to obtain
    # the percentage of epochs the node is selected to be active and in reserve
    # the function returns two vectors indexed by node id, with the % of epochs each node was active and in reserve
    # this function is the most resource-consuming (bottleneck) and could be substituted by a more efficient one
    def estimate_work_share_mixes(self, month):

        list_cumul = []  # cumulative stake ordered by node index
        cumul = 0.0
        for mix in self.list_mix[month]:
            cumul += mix.sigma_node
            list_cumul.append(cumul)

        # number of mixes actively routing packets in the mixnet
        mix_active = self.config.mixnet_layers * self.mixnet_width[month]
        mix_reserve = self.k[month] - mix_active

        activity_samples = {}  # dictionary of mix nodes
        for mix_id in range(self.num_mixes[month]):
            activity_samples[mix_id] = []  # per mix node : vector to track active and reserve epochs

        iterations = 30 * 24  # epochs in a month
        for epoch in range(iterations):
            current_active = []  # vector of mix nodes in the active set
            current_reserve = []  # vector of mix nodes in the reserve set
            list_cumul_temp = list_cumul[:]  # temporary copy of list_cumul

            # select the mix_active active nodes for the epoch (hour)
            while len(current_active) < mix_active:
                r = random.uniform(0, list_cumul_temp[-1])  # upper bound decreases as more nodes are picked
                candidate = next(i for i, x in enumerate(list_cumul_temp) if x >= r)
                if candidate not in current_active:
                    current_active.append(candidate)
                    if candidate == 0:
                        prob_candidate = list_cumul_temp[0]
                    else:
                        prob_candidate = list_cumul_temp[candidate] - list_cumul_temp[candidate - 1]
                    for i in range(candidate, len(list_cumul_temp)):
                        list_cumul_temp[i] -= prob_candidate  # update list_cumul_temp to eliminate picked node

            # select the mix_reserve reserve nodes for the epoch (hour)
            while len(current_reserve) < mix_reserve:
                r = random.uniform(0, list_cumul_temp[-1])
                candidate = next(i for i, x in enumerate(list_cumul_temp) if x >= r)
                if (candidate not in current_reserve) and (candidate not in current_active):
                    current_reserve.append(candidate)
                    if candidate == 0:
                        prob_candidate = list_cumul_temp[0]
                    else:
                        prob_candidate = list_cumul_temp[candidate] - list_cumul_temp[candidate - 1]
                    for i in range(candidate, len(list_cumul_temp)):
                        list_cumul_temp[i] -= prob_candidate  # update list_cumul_temp to eliminate picked node

            # add to the samples of the nodes whether they where active or in reserve in the epoch
            for active_mix in current_active:
                activity_samples[active_mix].append('A')
            for reserve_mix in current_reserve:
                activity_samples[reserve_mix].append('R')

        activity_vector = [0] * self.num_mixes[month]  # list with % of epochs in which each node has been active
        reserve_vector = [0] * self.num_mixes[month]  # list with % of epochs in which each node has been reserve
        for i in range(self.num_mixes[month]):
            activity_vector[i] = activity_samples[i].count('A') / iterations
            reserve_vector[i] = activity_samples[i].count('R') / iterations

        return activity_vector, reserve_vector

