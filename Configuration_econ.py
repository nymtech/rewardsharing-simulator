

# class contains ALL the input parameters that can be configured in the model. Set these parameters to desired values
# before passing a config object to Econ_results to obtain results for the configured scenario
class Config:
    def __init__(self):

        # nr of months of operation for which functions are computed. Example: 12 * 5 corresponds to 5 years
        self.num_intervals = 12 * 2 + 1  # number of monthly reward intervals considered

        # bandwidth growth and fees: key variable!
        # Set to BW_ZERO for no traffic and to BW_EXP_CAPPED_10%_HALVES_4x for slow growth (Input_Functions options)
        self.type_bw_growth = 'BW_ZERO'  # 'BW_ZERO'  'BW_EXP_CAPPED_10%_HALVES_4x' 'BW_EXP_GROWTH_6%_STEADY'
        self.initial_bandwidth = 200 * 10**3  # nr of packets/second in first month if type_bw_growth is _not_ BW_ZERO

        # token distribution parameters
        self.total_token = 10**9  # one billion token in total
        self.mixmining_pool_initial = 250 * 10**6   # 250 million token in the mixmining pool
        self.emission_rate = 0.02  # emit 2% of mixmining pool each month
        self.liquid_tokens_initial = 75 * 10**6  # liquid (circulating) tokens at the very beginning
        self.unvested_tokens_initial = 675 * 10**6  # token on vesting schedule
        self.vesting_period = 2 * 12  # vesting over 2 years
        self.vesting_interval = 3  # vesting 1/8th every 3 months

        # % of available token pledged and delegated to nodes (sum of both < 1.0, with the rest unallocated)
        self.frac_token_pledged = 0.15  # % of available token pledged to mix nodes
        self.frac_token_delegated = 0.60  # % of available token delegated by stakeholders to mix nodes run by others

        # percentage of bandwidth fees allocated to the set of mix nodes and to the set of gateways
        self.bw_to_mix = 0.6  # fraction of bw income that goes to mix nodes
        self.bw_to_gw = 1.0 - self.bw_to_mix  # fraction of bw income that goes to gateways

        # node parameters (these values are the same for all nodes)
        self.node_profit_margin = 0.1  # % of delegate rewards taken by the node operator (set by the node itself)
        self.node_performance = 1.0  # % of correctly routed packets (measured externally)
        self.minimum_pledge_mix = 1000  # in token, minimum pledge required to register as mix node

        # parameters for node stake distribution, reward algorithm, work factor
        self.frac_min_pledge_mix = 0.5  # % of total registered nodes that have the minimum pledge: key variable!
        self.frac_whale_mix = self.frac_token_pledged / 4  # % out of k (NOT total) of nodes with saturated pledge
        self.beta = 1.0  # percent of available stake needed to reach saturation for all nodes
        self.alpha = 0.30  # sybil-protection parameter in the reward algorithm (premium for larger pledge)
        self.factor_work_active = 10  # the work of active nodes is this factor's times the work of idle nodes

        # input function for token-dollar exchange rate (see Input_Functions_econ.py for pre-set functions)
        # extensions to add: token price functions that are a function of circulating token or other variables in
        # the system state of the previous interval
        self.type_token_growth = 'TOK_CONSTANT_100CENT'  # use constant value in baseline evaluations
        self.token_launch_price = 0.5  # price in dollar of one NYM at launch (ignored if type is TOK_CONSTANT_100CENT)

        # type of growth of price per packet (paid by end users of Nym)
        self.type_pp_growth = 'PP_CONSTANT'  # type of pricing change over time. Use 'PP_CONSTANT' for baseline case
        # bw pricing parameter: key variable! (key question: pricing per packet that makes the system viable long-term)
        self.price_packet_initial_dollar = 1 / 10**6  # $ per packet: price per packet paid by end users buying Nym bw

        # part of the operational cost for mix nodes (zero when nodes have flat operational rates with unlimited bw)
        self.cost_packet_bw_initial_dollar = 0  # dollar per packet paid by node operators (variable node bw costs)

        # minimum bw cost/month to account for loop dummy traffic costs (4k packets/second) when low/no user traffic
        # (TO-DO: this could be better integrated with per-interval updates, in case cost of bw not constant over time)
        self.cost_mix_dummy = self.cost_packet_bw_initial_dollar * 4000 * 3600 * 24 * 30

        # monthly flat costs of mix nodes
        self.monthly_cost_cpu_initial_dollar = 12.5  # $ per month per CPU (for a mix) as a flat monthly cost
        self.cpus_per_mix_initial = 8  # number of cpus per mix
        self.cpu_capacity_initial = 3125  # sphinx packets per second per cpu (from implementation benchmarks)

        # type growth parameters allow considering evolution over time (see Input_Functions_econ.py)
        self.type_cpu_cost_growth = 'COST_CPU_CONSTANT'  # evolution cost of one CPU
        self.type_packet_bw_cost_growth = 'COST_BW_CONSTANT'  # evolution cost of bandwidth for mix operators
        self.type_cpu_growth = 'N_CPU_CONSTANT'  # evolution number of cpus per mix
        self.type_capacity_growth = 'CPU_EXP_1%_STEADY'  # evolution packets per second processed per cpu

        # network size parameters, relevant to functions in Network_econ.py for setting the number of mix nodes
        self.mixnet_layers = 3  # number of layers
        self.type_mixnet_growth = 'MIXNET_LINEAR_GROWTH_WITH_TRAFFIC'  # nr of mixes: computed as function of traffic
        self.nr_min_mixes = 720  # k is never smaller than this number, regardless of (no) user traffic
        self.min_mixnet_width = 120  # minimum network width: determines the number of active mixes (LW)

        # mix_active_rate: key variable! provides tradeoff between "waste" of resources (unused mixes in reserve) and
        # capacity to grow fast if demand increases within the same month, without the need to adjust k (and re-stake)
        # a value of 1/2 implies on average half the selected (rewarded) nodes are active and the other half in reserve
        self.mix_active_rate = 1/2  # fraction of k mixes that are active, the rest are in "reserve" (MUST be <= 1)

        # peak_factor: key variable! determines another tradeoff between "waste" of resources (unused capacity per mix
        # on average) and capacity to serve peaks in demands when traffic is highly (and fast) variable
        # a value of 5 implies 5x peaks can be handled and average load: 1/5 = 20% -- and 80% idle cpu capacity
        self.peak_factor = 5  # size of traffic peaks over the average traffic load that can be handled at capacity

        # excess_candidate_factor: expect many more node node registrations than equilibrium value k. Beyond certain
        # point (bigger than 2), it does not make a diff in results of interest while slowing down sim
        self.excess_candidate_factor = 2  # multiplicative factor of actual mix candidates wrt to k (MUST be >= 1)

