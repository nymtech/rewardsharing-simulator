import cProfile
#import os
import pathlib
import string
import random
from Configuration_econ import Config
from Econ_Results_econ import Econ_Results
from Plot_Results_econ import Plot_Results
from Stakeholder_econ import Stakeholder

# returns the sequence number that corresponds to this execution (first simulation run will get '1' and so on)
# used to generate a directory to save the results of a simulation run
def get_sequence_number(filename='sequence.dat'):

    try:
        with open(filename, 'r') as f:
            seq_nr = int(f.read())
    except FileNotFoundError:
        seq_nr = 0
    seq_nr += 1
    # replace file contents with current sequence number (to be read during the next simulation run)
    with open(filename, 'w') as f:
        f.write(str(seq_nr))
    return seq_nr


# creates a randomly named directory (name with 6 char) inside the Figures folder
# returns the path of the directory (for saving files in it)
def create_dirs():

    seq_nr = get_sequence_number()
    output_dir = 'Output/' + 'simulation-run-' + str(seq_nr) + '/'
    output_dir = pathlib.Path.cwd() / output_dir
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
    figures_subdir = output_dir / 'Figures'
    pathlib.Path(figures_subdir).mkdir()
    return output_dir, figures_subdir


# saves the Configuration_econ.py file in the results directory, so that plots saved in the directory can be
# interpreted together with the configuration input values used to generate the results
def save_config_file(path):

    file_config = open('Configuration_econ.py')
    configuration = file_config.read()
    file_config.close()
    file_to_write = open(path / "config.txt", "w")
    file_to_write.write(configuration)
    file_to_write.close()


# returns True if the token amounts in the final epoch add up to the total amount of token, and exits otherwise
def sanity_check_results(results):

    # sanity check that the token amounts add up in the final epoch:
    total_token = int(round(results.mixmining_pool[-1] + results.circulating_tokens[-1] + results.unvested_tokens[-1]))
    if total_token != results.config.total_token:
        print("Total token doesn't add up!! Instead of a billion, the total is:", total_token)
        for i in range(len(results.mixmining_pool)):
            print("pool[", i, "]=", results.mixmining_pool[i], "circulating[", i, "]=", results.circulating_tokens[i],
                  "unvested[", i, "]=", results.unvested_tokens[i], "total=", results.mixmining_pool[i] +
                  results.circulating_tokens[i] + results.unvested_tokens[i])
        exit("ERROR in the simulation: the total token doesn't add up by the end of the run. Something is wrong.")
    else:
        return True


# prints to screen the parameter values of the mix node object passed to the function
def print_info_list_nodes(sample_month, results):

    print("\n================\n MONTH:", sample_month, "\n================\n")
    for mix in results.network.list_mix[sample_month]:
        print("mix node nr", mix.serial, "; sat level", mix.sat_level)
        print("node cost:", round(mix.node_cost))
        print("pledge:", round(mix.pledge), "; lambda", round(mix.lambda_node, 5))
        print("delegated:", round(mix.delegated), "; sigma", round(mix.sigma_node, 4))
        print("activity_percent=", round(100 * mix.activity_percent, 2), "%  ; reserve_percent=",
          round(100 * mix.reserve_percent, 2), "%")
        print("received rewards:", round(mix.received_rewards), "; operator profit:", round(mix.operator_profit),
          "; delegate profit:", round(mix.delegate_profit))
        print("ROS operator:", round(100 * mix.operator_profit / mix.pledge, 2), "%  ; annualized:",
              round(12 * 100 * mix.operator_profit / mix.pledge, 2), "%")
        if mix.delegated > 0:
            print("ROS delegator:", round(100 * mix.delegate_profit / mix.delegated, 2), "%  ; annualized:",
                  round(100 * 12 * mix.delegate_profit / mix.delegated, 2), "%")
        print("---")


# prints the info of the list of nodes existing in sample_month in a txt file
def save_info_list_nodes(sample_month, path, results):

    file_path = path / ("list_nodes_month" + str(sample_month) + ".txt")

    with open(file_path, "w") as f:
        f.write("-----\n")
        for mix in results.network.list_mix[sample_month]:
            f.write("mix node nr: " + str(mix.serial) + " ; sat level: " + str(mix.sat_level) + "\n")
            f.write("node cost: " + str(round(mix.node_cost)) + "\n")
            f.write("pledge: " + str(round(mix.pledge)) + " ; lambda: " + str(round(mix.lambda_node, 5)) + "\n")
            f.write("delegated: " + str(round(mix.delegated)) + " ; sigma: " + str(round(mix.sigma_node, 5)) + "\n")
            f.write("activity_percent: " + str(round(100 * mix.activity_percent, 2)) + "%")
            f.write(" ; reserve_percent: " + str(round(100 * mix.reserve_percent, 2)) + "% \n")
            f.write("received rewards: " + str(round(mix.received_rewards)))
            f.write(" ; operator profit: " + str(round(mix.operator_profit)))
            f.write(" ; delegate profit: " + str(round(mix.delegate_profit)) + "\n")
            f.write("Monthly returns operator: " + str(round(100 * mix.operator_profit / mix.pledge, 2)) + "%")
            f.write(" ; APY (annualized, no compound): " + str(round(12 * 100 * mix.operator_profit / mix.pledge, 2)) + "% \n")
            if mix.delegated > 0:
                f.write("Monthly returns delegator: " + str(round(100 * mix.delegate_profit / mix.delegated, 2)) + "%")
                f.write(" ; APY (annualized, no compound): " + str(round(100 * 12 * mix.delegate_profit / mix.delegated, 2)) + "% \n")
            f.write("-----\n")


def save_info_stakeholders(path, stakeholder):

    file_path = path / ("stakeholder_" + str(stakeholder.type_holder) + ".txt")

    with open(file_path, "w") as f:
        f.write("\n===\nType stakeholder: " + stakeholder.type_holder + "\n")
        f.write("liquid: " + str(stakeholder.liquid_stake) + "\n")
        f.write("unvested: " + str(stakeholder.unvested_stake) + "\n")
        f.write("\neffective stake: " + str(stakeholder.effective_stake) + "\n")
        f.write("effective compounded: " + str(stakeholder.effective_compounded_stake) + "\n")
        f.write("\ntotal: " + str(stakeholder.total_stake) + "\n")
        f.write("wealth compounded: " + str(stakeholder.wealth_compounded_stake) + "\n")
        f.write("\nrewards per month: " + str(stakeholder.rewards) + "\n")
        f.write("cumulative rewards: " + str(stakeholder.rewards_cumulative) + "\n")


# Plot pre-defined bw demand functions available in the Input_Functions library
def display_preset_functions(plot_res, save_to_file, path):

    file_path = None
    # plot pre-defined bandwidth growth functions
    if save_to_file:
        file_path = path / 'plot_preset_bw_growth_functions.png'
    plot_res.plot_preset_bw_growth_functions(file_path)


# This function contains the calls to plot figures with results of interest. If 'save_to_file' is True then files
# are saved in the directory specified in 'path'; otherwise plots are shown on screen.
# comment out  plot_res.plot_ functions that are not of interest in an evaluation
def display_save_plots(plot_res, save_to_file, path, config):

    max_years = config.num_intervals // 12
    max_quarters = config.num_intervals // 3

    ####################
    # FIGS TYPE 1: rewards relative to node stake saturation and stake/pledge distribution over nodes
    ####################

    # plot node, operator and delegate rewards relative to stake saturation (reputation) of the node
    file_path = None  # if value of path and filename is None then shows graphs on screen.
    vector_par_y = ['received_rewards', 'operator_profit', 'ROS_delegator', 'activity_percent', 'reserve_percent']
    par_x = 'saturation_percent'
    for quarter in range(max_quarters):  #for year in range(max_years):
        for par_y in vector_par_y:
            if save_to_file:
                file_path = path / ('scatter_' + par_y + '_vs_reputation_Q' + str(quarter+1) + '.png')
            plot_res.plot_scatter_par_y_vs_par_x(file_path, par_y, par_x, quarter)

    # plot node, operator and delegate rewards relative to pledge saturation of the node
    vector_par_y = ['received_rewards', 'operator_profit', 'ROS_delegator']
    par_x = 'pledge_saturation_percent'
    for quarter in range(max_quarters):  #for year in range(max_years):
        for par_y in vector_par_y:
            if save_to_file:
                file_path = path / ('scatter_' + par_y + '_vs_' + par_x + '_Q' + str(quarter+1) + '.png')
            plot_res.plot_scatter_par_y_vs_par_x(file_path, par_y, par_x, quarter)

    # plot the pledge/reputation distribution among nodes for a few sample months
    for year in range(0, max_years + 1):
        sample_month = max(0, (year-1)*12 + 11)
        if save_to_file:
            file_path = path / ('Distribution_month_' + str(sample_month) + '_')
        plot_res.plot_distribution_pledges_stake(file_path, sample_month)

    # plot rewards from pledging vs delegating a certain amount of stake to a node
    for stake in [10 ** 4, 10 ** 3, 100]:
        for quarter in range(1, max_quarters+1):  #for year in range(1, max_years + 1):
            if save_to_file:
                file_path = path / ('scatterplot_returns_staking_' + str(stake) + '_Q' + str(quarter) + '.png')
            plot_res.scatterplot_rewards_staking(file_path, stake, quarter)

    # Return on Stake for delegates: yearly delegate rewards divided by the amount of delegated stake (per node)
    for par in ['ROS_delegator_year']:
        if save_to_file:
            file_path = path / 'APY_delegates_annualized.png'
        plot_res.plot_yearly_ROS_distributions(file_path, par)

    ####################
    # FIGS TYPE 2: Plot distributions of values (boxplots) over nodes such as: node pledges, received rewards, profits
    # for operators / delegates, etc.
    # In the function plot_node_parameter_distributions(file_path, par) the inputs are:
    # file_path: pass None to show graphs on screen -- otherwise a .png file name to save the figure to file
    # par: parameter of interest to be shown, can take the values: 'pledge' 'delegated' 'total_stake' 'node_cost'
    # 'received_rewards' 'operator_profit' 'delegate_profit' 'sigma' 'lambda' 'ROS_operator' (monthly)
    # 'ROS_delegator' (monthly), 'activity_percent', 'reserve_percent', and more. Some illustrative examples below.
    ####################

    file_path = None  # if value of path and filename is None then shows graphs on screen.
    for par in ['pledge', 'total_stake', 'received_rewards', 'operator_profit', 'APY_delegator', 'activity_percent']:
        if save_to_file:
            file_path = path / ('nodes_distribution_' + str(par) + '.png')
        plot_res.plot_node_parameter_distributions(file_path, par)

    ####################
    # FIGS TYPE 3: Plot distributions of global system variables and averages (instead of per-node values/distributions)
    # List of available functions below.
    ####################

    # plot the amount of token in the mixmining pool, in circulation, and unvested
    if save_to_file:
        file_path = path / 'plot_vesting_circulating_token.png'
    plot_res.plot_vesting_circulating_token(file_path)

    # plot the cumulative net liquidity coming from the mixmining pool (accounting for unclaimed rewards)
    if save_to_file:
        file_path = path / 'plot_cumulative_mixmining_liquidity.png'
    plot_res.plot_cumulative_mixmining_liquidity(file_path)

    # plot the value of the stake saturation point (global value for all nodes, updated per interval)
    if save_to_file:
        file_path = path / 'plot_stake_saturation_node.png'
    plot_res.plot_stake_saturation_node(file_path)

    # plot the aggregate amount of rewards distributed and returned to the pool (unclaimed)
    if save_to_file:
        file_path = path / 'plot_rewards_distributed_unclaimed.png'
    plot_res.plot_rewards_distributed_unclaimed(file_path)

    # plot the bandwidth demand (note that this is a pre-set function chosen according to Configuration variables)
    if save_to_file:
        file_path = path / 'plot_total_bw.png'
    if config.type_bw_growth != 'BW_ZERO':  # if 'BW_ZERO' it's simply constant at zero, nothing to plot
        plot_res.plot_total_bw(file_path)

    # plot the number of operators of each type over time (if 'BW_ZERO' it's simply constant value in config)
    if save_to_file:
        file_path = path / 'plot_nr_operators.png'
    if config.type_bw_growth != 'BW_ZERO':
        plot_res.plot_nr_operators(file_path)


def stakeholder_plots(plot_res, save_to_file, path, config):

    file_path = None
    median_ROS = plot_res.results.get_median_ROS_reputable_node()
    if save_to_file:
        file_path = path / 'median_ROS_high_rep_nodes.png'
    plot_res.plot_median_ROS(file_path, median_ROS)
    print("median ROS:" + str(median_ROS))

    stakeholders = ['TESTNET', 'OPTION_1', 'OPTION_2', 'VALIDATOR_100k', 'VALIDATOR_200k', 'VALIDATOR_400k',
                    'WHALE_1M', 'WHALE_10M', 'WHALE_80M']
    for s in stakeholders:
        stakeholder = Stakeholder(s, config)
        stakeholder.compute_rewards(median_ROS)
        if save_to_file:
            file_path = path / ('stakeholder_' + s + '.png')
        plot_res.plot_stakeholder_staking(file_path, stakeholder)
        save_info_stakeholders(path, stakeholder)

# main function that instantiates the classes to run a simulation of the system with a the given configuration
def run_model(save_to_file):

    # depending on save_to_file, create a randomly named directory for saving figures, or set path to empty
    if save_to_file:
        output_dir, figures_subdir = create_dirs()  # create a randomly name directory to store the figures
        save_config_file(output_dir)  # saves the configuration parameters in a file config.txt
    else:
        output_dir, figures_subdir = None, None  # show data / figs on screen instead of saving them to files

    # FIRST create configuration object with all the input variables
    config = Config()

    # SECOND create and run the model with the chosen configuration, perform basic sanity check on results
    results = Econ_Results(config)
    sanity_check_results(results)

    # THIRD create the plotting object to plot results (that can be displayed or saved to file)
    plot_res = Plot_Results(results)

    # FOURTH call the desired plotting functions to look into system variables and results of interest
    display_save_plots(plot_res, save_to_file, figures_subdir, config)

    # FIFTH print the list of nodes for a month to see if all node variables look ok
    for sample_month in [0]:#[0, 11]:
        if save_to_file:  # save info in a file
            save_info_list_nodes(sample_month, output_dir, results)
        else:  # print the info to screen
            print_info_list_nodes(sample_month, results)

    # SIXTH compute results for specific stakeholders
    #stakeholder_plots(plot_res, save_to_file, path, config)


if __name__ == '__main__':

    save_results_to_file = True  # True / False : if True, plots are saved to file, if False, they are shown on screen
    run_model(save_results_to_file)
    #cProfile.run('run_model(save_results_to_file)')
