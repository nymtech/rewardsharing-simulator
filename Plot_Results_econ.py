import math
import numpy as np
import matplotlib.pyplot as plt


# This class takes a results object and provides a library of plot functions to visualize results of interest
# The plots can be shown on screen (by passing file_name='' to the functions) or saved to a file
# The first set of functions show results of a run of the model, while the last functions plot the library of
# pre-defined input functions for different variables

class Plot_Results:
    def __init__(self, results):
        self.results = results
        self.config = results.config

    # stake is the available stake to pledge or delegate
    # creates scatterplots with returns the stakeholder would have obtained pledging/delegating that amount to mix nodes
    # samples mix nodes with amounts of pledge/delegation compatible with the specified stake in the specified year
    def scatterplot_rewards_staking(self, file_name, stake, quarter):

        rewards = self.results.sample_quarterly_rewards_no_compound_vs_saturation(stake)
        sequence_x_vals_pledge = []
        sequence_y_vals_pledge = []
        sequence_x_vals_del = []
        sequence_y_vals_del = []
        for month in range(3*(quarter-1), 3*quarter):  # range(self.config.num_intervals):
            for i in range(len(rewards['pledge-mix'][month])):
                value_y = rewards['pledge-mix'][month][i]
                value_x = rewards['sat-pledge-mix'][month][i]
                sequence_y_vals_pledge.append(value_y)
                sequence_x_vals_pledge.append(value_x)
            for i in range(len(rewards['delegate-mix'][month])):
                value_y = rewards['delegate-mix'][month][i]
                value_x = rewards['sat-delegate-mix'][month][i]
                sequence_y_vals_del.append(value_y)
                sequence_x_vals_del.append(value_x)

        fig = plt.figure(figsize=(10, 8), dpi=90, facecolor='w', edgecolor='k')
        ax = fig.add_subplot()

        if stake == 1000:
            inv_str = '1k'
        elif stake == 10000:
            inv_str = '10k'
        elif stake == 100000:
            inv_str = '100k'
        elif stake == 1000000:
            inv_str = '1 million'
        else:
            inv_str = str(stake)

        ax.scatter(sequence_x_vals_del, sequence_y_vals_del, s=100, alpha=0.5, c='tab:orange', label='delegation of ' + inv_str + ' NYM')
        ax.scatter(sequence_x_vals_pledge, sequence_y_vals_pledge, s=100, alpha=0.7, c='tab:green', label='pledge of ' + inv_str + ' NYM')

        ax.axhline(y=0, color='r', linewidth=1, linestyle='-')
        ax.set_ylabel('Q' + str(quarter) + ': Quarterly rewards for staking ' + inv_str + ' NYM ', fontsize=14)
        ax.set_xlabel('node stake saturation (node reputation)', fontsize=14)
        plt.setp(ax.get_yticklabels(), fontsize=14)
        plt.setp(ax.get_xticklabels(), fontsize=14)
        plt.xlim([0, 1])

        #plt.gca().set_ylim(bottom=-2800)

        ax.legend()
        ax.grid(True)
        if len(file_name) < 2:
            plt.show()
        else:
            plt.savefig(file_name)
        plt.close()

    # This function produces a scatterplot where each point has x,y coordinates as indicated in the inputs par_x, par_y
    # selects results for the 12 months of the specified year
    # annualizes results by multiplying monthly results by 12 (no compounding effects accounted for)
    def plot_scatter_par_y_vs_par_x(self, file_name, par_y, par_x, quarter):

        sequence_containing_x_vals = []
        sequence_containing_y_vals = []
        for month in range(quarter*3, (quarter+1)*3):
            for node in self.results.network.list_mix[month]:
                val_y = self.results.get_node_value(node, par_y)
                if par_y in ['received_rewards', 'operator_profit', 'ROS_delegator'] and val_y is not None:
                    val_y = 12 * val_y  # annualize the profits / ROS
                val_x = self.results.get_node_value(node, par_x)
                sequence_containing_x_vals.append(val_x)
                sequence_containing_y_vals.append(val_y)

        fig = plt.figure(figsize=(10, 8), dpi=90, facecolor='w', edgecolor='k')
        ax = fig.add_subplot()
        plt.scatter(sequence_containing_x_vals, sequence_containing_y_vals)
        ax.axhline(y=0, color='r', linewidth=1, linestyle='-')
        ax.set_ylabel('Mix nodes:  ' + par_y + '  vs  ' + par_x, fontsize=14)
        ax.set_xlabel(par_x + ' Q' + str(quarter+1), fontsize=14)
        plt.setp(ax.get_yticklabels(), fontsize=14)
        plt.setp(ax.get_xticklabels(), fontsize=14)
        if len(file_name) < 2:
            plt.show()
        else:
            plt.savefig(file_name)
        plt.close()

    # plots annualized ROS for operators / delegators of nodes of type_node owned by owner
    def plot_yearly_ROS_distributions(self, file_name, par):

        if par == 'ROS_delegator_year':  # clean up the None
            dict_par = self.results.get_dictionary_distribution('ROS_delegator')
            for month in range(self.config.num_intervals):
                dict_par[month] = [i for i in dict_par[month] if i is not None]
        elif par == 'ROS_operator_year':
            dict_par = self.results.get_dictionary_distribution('ROS_operator')
        else:
            dict_par = {}
            print("wrong parameter name for yearly ROS distribution")
            exit("issue in call to plot_yearly_ROS_distributions()")

        dict_year = {}
        num_years = math.floor(self.config.num_intervals / 12)
        for year in range(num_years):
            dict_year[year] = []
            for month in range(year*12, year*12 + 12):
                annualized_ros = np.multiply(dict_par[month], 12)
                dict_year[year].extend(annualized_ros)

        fig = plt.figure(figsize=(10, 8), dpi=90, facecolor='w', edgecolor='k')
        ax = fig.add_subplot()
        ax.boxplot([dict_year[i] for i in range(len(dict_year))], showfliers=True)
        ax.axhline(y=0, color='r', linewidth=1, linestyle='-')
        ax.set_xlabel('interval (yearly)', fontsize=14)
        plt.setp(ax.get_xticklabels(), fontsize=14)
        plt.setp(ax.get_yticklabels(), fontsize=14)
        #if par == 'ROS_delegator_year':
        #    plt.gca().set_ylim(bottom=-0.005, top=0.2)
            #plt.gca().set_ylim(bottom=-5, top=15)

        if par == 'ROS_delegator_year':
            par = 'APY (no compound) delegates'
        ax.set_ylabel('distribution of: ' + str(par), fontsize=14)
        if len(file_name) < 2:
            plt.show()
        else:
            plt.savefig(file_name)
        plt.close()

    # Distribution of a variable (shown as boxplots) in a set of nodes, one boxplot per interval
    # if file_name = '' (empty) the function plots on screen, if file_name provided, fig is saved to file_name
    # par is the parameter of interest that we want to display. Possible values are: 'pledge' 'delegated' 'total_stake'
    # 'node_cost' 'received_rewards' 'operator_profit' 'delegate_profit' 'sigma' 'lambda' 'ROS_operator' 'ROS_delegator'
    def plot_node_parameter_distributions(self, file_name, par):

        dict_par = self.results.get_dictionary_distribution(par)
        if par == 'ROS_delegator' or par == 'delegate_profit' or par == 'APY_delegator':  # clean up the None
            for month in range(self.config.num_intervals):
                dict_par[month] = [i for i in dict_par[month] if i is not None]

        fig = plt.figure(figsize=(10, 8), dpi=90, facecolor='w', edgecolor='k')
        ax = fig.add_subplot()
        ax.boxplot([dict_par[i] for i in range(len(dict_par))], showfliers=True)
        ax.axhline(y=0, color='r', linewidth=1, linestyle='-')

        years = int(round(self.config.num_intervals / 12))
        xmin, xmax = ax.get_xlim()
        custom_ticks = np.linspace(xmin, xmax, 1+2*years, dtype=int)
        ax.set_xticks(custom_ticks)
        ax.set_xticklabels(custom_ticks, fontsize=14)
        plt.setp(ax.get_yticklabels(), fontsize=14)
        ax.set_xlabel('interval (monthly)', fontsize=14)
        ax.set_ylabel('distribution of: ' + str(par), fontsize=14)
        #ax.yticks(fontsize=14)
        #ax.xaxis.set_major_locator(plt.MaxNLocator(years*2))
        #ax.locator_params(axis='x', nbins=years*4)
        #if par in ['received_rewards', 'operator_profit']:
        #    plt.gca().set_ylim(bottom=-300, top=11000)
        #elif par in ['pledge', 'total_stake']:
        #    plt.gca().set_ylim(bottom=-20000, top=1300000)

        if len(file_name) < 2:
            plt.show()
        else:
            plt.savefig(file_name)
        plt.close()

    # plots the median return on stake for nodes with >0.9 saturation
    def plot_median_ROS(self, file_name, median_ROS):
        annualized_ROS = []
        for val in median_ROS:
            annualized_ROS.append(val*12)
        fig = plt.figure(figsize=(10, 8), dpi=90, facecolor='w', edgecolor='k')
        ax = fig.add_subplot()
        ax.plot(annualized_ROS, '-', linewidth=2, label='annualized reward rate')
        ax.set_xlabel('interval (monthly)', fontsize=14)
        ax.set_ylabel('Annualized reward rate (median for delegates of high reputation nodes)', fontsize=14)
        plt.setp(ax.get_xticklabels(), fontsize=14)
        plt.setp(ax.get_yticklabels(), fontsize=14)
        ax.legend()
        ax.axhline(y=0, color='r', linewidth=1, linestyle='-')
        if len(file_name) < 2:
            plt.show()
        else:
            plt.savefig(file_name)
        plt.close()

    # plots the stake of the given stakeholder
    def plot_stakeholder_staking(self, file_name, stakeholder):
        fig = plt.figure(figsize=(10, 8), dpi=90, facecolor='w', edgecolor='k')
        ax = fig.add_subplot()
        ax.plot(stakeholder.wealth_compounded_stake, '-', linewidth=2, label='total stake (compounded wealth)')
        ax.plot(stakeholder.unvested_stake, '-', linewidth=1, label='unvested stake')
        ax.plot(stakeholder.rewards_cumulative, '-', linewidth=2, label='cumulative rewards')

        ax.set_xlabel('interval (monthly)', fontsize=14)
        ax.set_ylabel('Rewards for participant: ' + stakeholder.type_holder, fontsize=14)
        plt.setp(ax.get_xticklabels(), fontsize=14)
        plt.setp(ax.get_yticklabels(), fontsize=14)
        ax.legend()
        ax.axhline(y=0, color='r', linewidth=1, linestyle='-')
        if len(file_name) < 2:
            plt.show()
        else:
            plt.savefig(file_name)
        plt.close()

    # plots the maximum amount of stake per mix node (saturation point)
    def plot_stake_saturation_node(self, file_name):

        fig = plt.figure(figsize=(10, 8), dpi=90, facecolor='w', edgecolor='k')
        ax = fig.add_subplot()
        ax.plot(self.results.stake_saturation_mix, '-', linewidth=2, label='stake saturation')
        ax.set_xlabel('interval (monthly)', fontsize=14)
        ax.set_ylabel('Stake saturation point for mix nodes', fontsize=14)
        plt.setp(ax.get_xticklabels(), fontsize=14)
        plt.setp(ax.get_yticklabels(), fontsize=14)
        ax.legend()
        ax.axhline(y=0, color='r', linewidth=1, linestyle='-')
        if len(file_name) < 2:
            plt.show()
        else:
            plt.savefig(file_name)
        plt.close()

    # plot cumulative liquidity emitted from the mixmining pool
    def plot_cumulative_mixmining_liquidity(self, file_name):

        cumul = self.results.mixmining_pool[0] - self.results.mixmining_pool[1]
        cumulative_emissions = [cumul]
        for i in range(1, self.config.num_intervals):
            cumul += self.results.mixmining_pool[i-1] - self.results.mixmining_pool[i]
            cumulative_emissions.append(cumul)

        fig = plt.figure(figsize=(10, 8), dpi=90, facecolor='w', edgecolor='k')
        ax = fig.add_subplot()

        ax.plot(cumulative_emissions, '-', linewidth=2, label='Cumulative mixmining emissions')
        ax.plot(self.results.mixmining_emitted, '--', linewidth=1, label='Mixmining emissions per interval')
        ax.plot(self.results.rewards_distributed_mix, '-', linewidth=1, label='Mixmining rewards distributed')
        ax.plot(self.results.rewards_unclaimed, ':', linewidth=1, label='Unclaimed rewards (returned to pool)')

        ax.axhline(y=0, color='r', linewidth=1, linestyle='-')
        ax.set_xlabel('interval (monthly)', fontsize=14)
        ax.set_ylabel('amount of token', fontsize=14)
        plt.setp(ax.get_xticklabels(), fontsize=14)
        plt.setp(ax.get_yticklabels(), fontsize=14)
        ax.legend()
        #plt.gca().set_ylim(bottom=-10**4, top=15*10**6)
        if len(file_name) < 2:
            plt.show()
        else:
            plt.savefig(file_name)
        plt.close()

    # plot total income to the network including the split between emitted mixmining rewards and collected bw fees
    # plot rewards rewards distributed and rewards unclaimed (thus returned to mixmining pool)
    def plot_rewards_distributed_unclaimed(self, file_name):

        fig = plt.figure(figsize=(10, 8), dpi=90, facecolor='w', edgecolor='k')
        ax = fig.add_subplot()
        if self.config.type_bw_growth == 'BW_ZERO':
            ax.plot(self.results.income_global_mix, '-', linewidth=2, label='R(t): Budget mixnet rewards (mixmining)')
        else:
            ax.plot(self.results.income_global_mix, '-', linewidth=2, label='R(t): Budget mixnet rewards (mixmining+fees)')
            ax.plot(self.results.share_income_bw_mix, '-', linewidth=1, label='0.6*F(t): Bw fees for mixnet')
            ax.plot(self.results.mixmining_emitted, '-', linewidth=1, label='0.02*P(t): Mixmining rewards')
        ax.plot(self.results.rewards_distributed_mix, ':', linewidth=2, label='Σ Ri(t): Rewards distributed')
        ax.plot(self.results.rewards_unclaimed, ':', linewidth=2, label='U(t): Unclaimed rewards')
        ax.axhline(y=0, color='r', linewidth=1, linestyle='-')
        ax.set_xlabel('interval (monthly)', fontsize=14)
        ax.set_ylabel('amount of token', fontsize=14)
        plt.setp(ax.get_xticklabels(), fontsize=14)
        plt.setp(ax.get_yticklabels(), fontsize=14)
        ax.legend()
        #plt.gca().set_ylim(bottom=-10**4, top=15*10**6)
        if len(file_name) < 2:
            plt.show()
        else:
            plt.savefig(file_name)
        plt.close()

    # plots the amount of token in the mixmining pool, in circulation, and unvested
    def plot_vesting_circulating_token(self, file_name):

        fig = plt.figure(figsize=(10, 8), dpi=90, facecolor='w', edgecolor='k')
        ax = fig.add_subplot()
        ax.plot(self.results.mixmining_pool, '-', linewidth=1, label='mixmining pool')
        ax.plot(self.results.circulating_tokens, '-', linewidth=1, label='circulating tokens')
        ax.plot(self.results.unvested_tokens, ':', linewidth=1, label='unvested token')
        ax.set_xlabel('interval (monthly)', fontsize=14)
        ax.set_ylabel('amount of token (vested, circulating, in mixmining pool)', fontsize=14)
        plt.setp(ax.get_xticklabels(), fontsize=14)
        plt.setp(ax.get_yticklabels(), fontsize=14)
        ax.legend()
        #plt.gca().set_ylim(bottom=0)
        if len(file_name) < 2:
            plt.show()
        else:
            plt.savefig(file_name)
        plt.close()

    # plots the considered bandwidth demand (pre-set input function configured in Config)
    def plot_total_bw(self, file_name):

        fig = plt.figure(figsize=(10, 8), dpi=90, facecolor='w', edgecolor='k')
        ax = fig.add_subplot()
        ax.plot(self.results.network.bw_demand, '-', linewidth=1, label='nr packets demanded per month')
        ax.set_xlabel('interval (monthly)', fontsize=14)
        ax.set_ylabel('total demanded bandwidth (nr of packets)', fontsize=14)
        plt.setp(ax.get_xticklabels(), fontsize=14)
        plt.setp(ax.get_yticklabels(), fontsize=14)
        ax.legend()
        #plt.gca().set_ylim(bottom=0)
        if len(file_name) < 2:
            plt.show()
        else:
            plt.savefig(file_name)
        plt.close()

    # plot the number of mix nodes nodes over time
    # the number follows the bandwidth demand in the network (grows from a minimum with demand)
    def plot_nr_operators(self, file_name):

        fig = plt.figure(figsize=(10, 8), dpi=90, facecolor='w', edgecolor='k')
        ax = fig.add_subplot()
        ax.plot(self.results.network.num_mixes, '-', linewidth=1, label='nr of registered mixes')
        ax.set_xlabel('interval (monthly)', fontsize=14)
        ax.set_ylabel('number of registered node operators', fontsize=14)
        plt.setp(ax.get_xticklabels(), fontsize=14)
        plt.setp(ax.get_yticklabels(), fontsize=14)
        ax.legend()
        #plt.gca().set_ylim(bottom=0)
        if len(file_name) < 2:
            plt.show()
        else:
            plt.savefig(file_name)
        plt.close()

    # produces two figures corresponding to the specified month
    # the first figure shows the distribution of reputation (decreasing order) and its corresponding pledge per node
    # the second figure shows the distribution of pledges (in decreasing size) for the node set
    def plot_distribution_pledges_stake(self, file_name, month):

        nr_mixes = len(self.results.network.list_mix[month])
        pledges = []
        total = []
        for mix in self.results.network.list_mix[month]:
            pledges.append(mix.pledge)
            total.append(mix.delegated + mix.pledge)

        ordered_pledges = []
        ordered_total = []
        for i in range(nr_mixes):
            max_val = max(total)
            ind_val = total.index(max_val)
            ordered_total.append(max_val)
            ordered_pledges.append(pledges[ind_val])
            total[ind_val] = 0
            pledges[ind_val] = 0

        list_y = [ordered_total, ordered_pledges]
        labels_y = ['total stake (pledged + delegated)', 'pledged']
        title = "distribution pledge and delegation over nodes"
        fig = plt.figure(figsize=(10, 8), dpi=90, facecolor='w', edgecolor='k')
        ax = fig.add_subplot()
        i = 0
        t = ['-', '-']
        w = [2, 1]
        c = ['g', 'b']
        for y in list_y:
            ax.plot(y, t[i], color=c[i], linewidth=w[i], label=str(labels_y[i]))
            i += 1
        ax.set_xlabel('Registered nodes (ordered by reputation)', fontsize=12)
        ax.set_ylabel(title, fontsize=12)
        ax.axhline(y=0, color='r', linewidth=1, linestyle='-')
        k = self.results.network.k[month]
        ax.axvline(x=k, color='tab:brown', linewidth=2, linestyle='--')
        ax.legend()
        #plt.gca().set_ylim(bottom=-10000)
        if len(file_name) < 2:
            plt.show()
        else:
            plt.savefig(file_name + 'total_stake.png')
        plt.close()

        ordered_by_pledge = sorted(ordered_pledges, reverse=True)

        fig = plt.figure(figsize=(10, 8), dpi=90, facecolor='w', edgecolor='k')
        ax = fig.add_subplot()
        ax.plot(ordered_by_pledge, '-', linewidth=2, label="pledge")
        ax.set_xlabel("Registered nodes (ordered by pledge)", fontsize=12)
        ax.axhline(y=0, color='r', linewidth=1, linestyle='-')
        ax.legend()
        if len(file_name) < 2:
            plt.show()
        else:
            plt.savefig(file_name + 'pledge.png')
        plt.close()

    # Plot pre-defined bandwidth growth functions that are available in Input_Functions
    # useful to see which functions are available and which one to choose for scenarios with more or less bw demand
    def plot_preset_bw_growth_functions(self, file_name):

        # add types if needed: check Input_Functions_econ.py and see types starting with 'BW_'
        types = ['BW_EXP_CAPPED_10%_HALVES_10x', 'BW_EXP_CAPPED_10%_DROP1/3_4x', 'BW_EXP_GROWTH_6%_STEADY',
                 'BW_EXP_CAPPED_10%_HALVES_4x', 'BW_LINEAR_GROWTH_10kps', 'BW_EXP_GROWTH_10%_DROP1/4_6M',
                 'BW_EXP_GROWTH_10%_HALVES_6M', 'BW_EXP_GROWTH_10%_HALVES_12M', 'BW_ZERO']
        dict_functions = self.get_dictionary_functions(types)

        fig = plt.figure(figsize=(10, 8), dpi=90, facecolor='w', edgecolor='k')
        ax = fig.add_subplot()
        for t in types:
            ax.plot(dict_functions[t], '-', linewidth=2, label=t)
        ax.set_xlabel('interval (monthly)', fontsize=14)
        ax.set_ylabel('bandwidth growth functions (nr packets / month)', fontsize=14)
        plt.setp(ax.get_xticklabels(), fontsize=14)
        plt.setp(ax.get_yticklabels(), fontsize=14)
        ax.legend()
        #plt.gca().set_ylim(bottom=0)
        if len(file_name) < 2:
            plt.show()
        else:
            plt.savefig(file_name)
        plt.close()

    # function takes a vector of function type strings and returns a dictionary with the functions, indexed by
    # their type string
    def get_dictionary_functions(self, types):

        dict_functions = {}
        for t in types:
            y = self.results.input_functions.get_function(t)
            dict_functions.update({t: y})
        return dict_functions
