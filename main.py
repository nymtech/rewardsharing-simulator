import cProfile
import os
import string
import random
from Configuration_econ import Config
from Econ_Results_econ import Econ_Results
from Plot_Results_econ import Plot_Results

# returns a random character string of a given length
# used to generate a randomly named directory to save the results of a simulation run
def get_random_string(length):
    # choose from all lowercase, uppercase and numbers
    letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


# creates a randomly named directory (name with 6 char) inside the Figures folder
# returns the path of the directory (for saving files in it)
# triggers an error if a "Figures" folder does not exist in the directory where the main script is running
def create_dir():

    rnd_dir = get_random_string(6)
    path = 'Figures/' + rnd_dir + '/'
    try:
        os.mkdir(path)
    except OSError:
        print("Creation of the directory %s failed" % path)
        print("Make sure a Figures folder exists")
    else:
        print("Successfully created the directory %s " % path)
    return path


# saves the Configuration_econ.py file in the results directory, so that plots saved in the directory can be
# interpreted together with the configuration input values used to generate the results
def save_config_file(path):

    file_config = open('Configuration_econ.py')
    configuration = file_config.read()
    file_config.close()
    file_to_write = open(path + "config.txt", "w")
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
def print_info_node(mix):
    print("mix node nr", mix.serial, "; sat level", mix.sat_level, "; node cost:", round(mix.node_cost))
    print("pledge:", round(mix.pledge), "; lambda", round(mix.lambda_node, 5), "; delegated:", round(mix.delegated),
          "; sigma", round(mix.sigma_node, 4))
    print("activity_percent=", round(100 * mix.activity_percent, 2), "%  ; reserve_percent=",
          round(100 * mix.reserve_percent, 2), "%")
    print("received rewards:", round(mix.received_rewards), "; operator profit:", round(mix.operator_profit),
          "; delegate profit:", round(mix.delegate_profit))
    print("ROS operator:", round(100 * mix.operator_profit / mix.pledge, 2),
          "%  ; annualized:", round(12 * 100 * mix.operator_profit / mix.pledge, 2), "%")
    if mix.delegated > 0:
        print("ROS delegator:", round(100 * mix.delegate_profit / mix.delegated, 2),
              "%  ; annualized:", round(100 * 12 * mix.delegate_profit / mix.delegated, 2), "%")


# Plot pre-defined bw demand functions available in the Input_Functions library
def display_preset_functions(plot_res, save_to_file, path):

    file_name = ''
    # plot pre-defined bandwidth growth functions
    if save_to_file:
        file_name = 'plot_preset_bw_growth_functions.png'
    plot_res.plot_preset_bw_growth_functions(path + file_name)


# This function contains the calls to plot figures with results of interest. If 'save_to_file' is True then files
# are saved in the directory specified in 'path'; otherwise plots are shown on screen.
# comment out  plot_res.plot_ functions that are not of interest in an evaluation
def display_save_plots(plot_res, save_to_file, path, config):

    file_name = ''  # if value of path and filename is '' then shows graphs in screen.
    max_years = config.num_intervals // 12

    ####################
    # FIGS TYPE 1: rewards relative to node stake saturation and stake/pledge distribution over nodes
    ####################

    # plot node, operator and delegate rewards relative to stake/pledge saturation of the node
    vector_par_y = ['received_rewards', 'operator_profit', 'ROS_delegator']
    vector_par_x = ['saturation_percent', 'pledge_saturation_percent']
    for year in range(max_years):
        for par_y in vector_par_y:
            for par_x in vector_par_x:
                if save_to_file:
                    file_name = 'scatter_' + par_y + '_vs_' + par_x + '_y' + str(year+1) + '.png'
                plot_res.plot_scatter_par_y_vs_par_x(path + file_name, par_y, par_x, year)

    # plot the pledge/reputation distribution among nodes for a few sample months
    for year in range(0, max_years + 1):
        sample_month = max(0, (year-1)*12 + 11)
        if save_to_file:
            file_name = 'Distribution_month_' + str(sample_month) + '_'
        plot_res.plot_distribution_pledges_stake(path + file_name, sample_month)

    # plot rewards from pledging vs delegating a certain amount of stake to a node
    for stake in [10 ** 6, 10 ** 5, 10 ** 4, 10 ** 3]:
        for year in range(1, max_years + 1):
            if save_to_file:
                file_name = 'scatterplot_returns_staking_' + str(stake) + '_y' + str(year) + '.png'
            plot_res.scatterplot_rewards_staking(path + file_name, stake, year)

    # Return on Stake for delegates: yearly delegate rewards divided by the amount of delegated stake
    for par in ['ROS_delegator_year']:
        if save_to_file:
            file_name = 'ROS_delegates_annualized.png'
        plot_res.plot_yearly_ROS_distributions(path + file_name, par)

    ####################
    # FIGS TYPE 2: Plot distributions of values (boxplots) over nodes such as: node pledges, received rewards, profits
    # for operators / delegates, etc.
    # In the function plot_node_parameter_distributions(file_name, type_node, owner, par) the inputs are:
    # file_name: pass empty value '' to show graphs on screen -- otherwise a .png file name to save the figure to file
    # par: parameter of interest to be shown, can take the values: 'pledge' 'delegated' 'total_stake' 'node_cost'
    # 'received_rewards' 'operator_profit' 'delegate_profit' 'sigma' 'lambda' 'ROS_operator' (monthly)
    # 'ROS_delegator' (monthly). Some illustrative examples below.
    ####################

    file_name = ''  # if value of path and filename is '' then shows graphs in screen.
    for par in ['pledge', 'total_stake', 'received_rewards', 'operator_profit', 'ROS_delegator', 'activity_percent']:
        if save_to_file:
            file_name = 'nodes_distribution_' + str(par) + '.png'
        plot_res.plot_node_parameter_distributions(path + file_name, par)

    ####################
    # FIGS TYPE 3: Plot distributions of global system variables and averages (instead of node specific values)
    # List of available functions below.
    ####################

    # plot the amount of token in the inflation pool, in circulation, and vested
    if save_to_file:
        file_name = 'plot_vesting_circulating_token.png'
    plot_res.plot_vesting_circulating_token(path + file_name)

    # plot the net liquidity coming from the mixmining pool
    if save_to_file:
        file_name = 'plot_cumulative_mixmining_liquidity.png'
    plot_res.plot_cumulative_mixmining_liquidity(path + file_name)

    # plot the value of saturation stake per node
    if save_to_file:
        file_name = 'plot_stake_saturation_node.png'
    plot_res.plot_stake_saturation_node(path + file_name)

    # plot the amount of rewards distributed to operators (in aggregate) and returned to the pool (unclaimed)
    if save_to_file:
        file_name = 'plot_rewards_distributed_unclaimed.png'
    plot_res.plot_rewards_distributed_unclaimed(path + file_name)

    # plot the bandwidth demand (note that this is a pre-set function chosen according to Configuration variables)
    if save_to_file:
        file_name = 'plot_total_bw.png'
    if config.type_bw_growth != 'BW_ZERO':  # if 'BW_ZERO' it's simply constant at zero
        plot_res.plot_total_bw(path + file_name)

    # plot the number of operators of each type over time (if 'BW_ZERO' it's simply constant value in config)
    if save_to_file:
        file_name = 'plot_nr_operators.png'
    if config.type_bw_growth != 'BW_ZERO':
        plot_res.plot_nr_operators(path + file_name)


def run_model(save_to_file):

    # depending on save_to_file, create a randomly named directory for saving figures, or set path to empty
    if save_to_file:
        path = create_dir()  # create a randomly name directory to store the figures
        save_config_file(path)  # saves the configuration parameters in a file config.txt
    else:
        path = ''  # empty path and file_name will show figs on screen instead of saving them to file

    # FIRST create configuration object with all the input variables
    config = Config()

    # SECOND create and run the model with the chosen configuration, perform basic sanity check on results
    results = Econ_Results(config)
    sanity_check_results(results)

    # THIRD create the plotting object to plot results (that can be displayed or saved to file)
    plot_res = Plot_Results(results)

    # FOURTH call the desired plotting functions to look into system variables and results of interest
    display_save_plots(plot_res, save_to_file, path, config)

    # print the list of nodes for a month to see if all variables look ok
    for sample_month in [11]:
        print("\n MONTH", sample_month)
        print("================\n")
        for node in results.network.list_mix[sample_month]:
            print_info_node(node)
            print("---")


if __name__ == '__main__':

    # decide if results are to be shown on screen or saved to png files
    save_results_to_file = True  # True / False : if True, plots are saved to file, if False, they are shown on screen

    run_model(save_results_to_file)
    #cProfile.run('run_model(save_results_to_file)')
