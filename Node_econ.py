
# class contains the variables of interest for a mix node that lives during one epoch
# the list of nodes for each epoch is kept in Network_econ.py
class Node:
    def __init__(self, serial, sat_level, pledge, profit_margin, performance, node_cost, stake_saturation):
        self.serial = serial  # serial nr of the node of its type
        self.sat_level = sat_level  # 'SAT', 'MIN', 'RND'
        self.pledge = pledge  # amount token pledged by the node operator
        self.profit_margin = profit_margin  # profit margin set by the node operator (between 0 and 1)
        self.performance = performance  # measured performance of the node (between 0 and 1)
        self.node_cost = node_cost  # monthly operational cost of the node as declared by the node operator
        self.stake_saturation = stake_saturation  # saturation point per node in the interval (global value)
        self.delegated = 0  # amount of delegated stake. This is updated after object creation.
        self.lambda_node = 0  # ratio of pledge to total stake. Updated after delegated stake has been set.
        self.sigma_node = 0  # ratio of delegated to total stake. Updated after delegated stake has been set.
        self.activity_percent = 0  # fraction of epochs in the interval where the node is active
        self.reserve_percent = 0  # fraction of epochs in the interval where the node is in reserve
        self.received_rewards = 0  # rewards actually received by the node
        self.operator_profit = 0  # profit given to the operator (who in addition is also refunded for the node costs)
        self.delegate_profit = 0  # aggregate profits given to the set of delegates for all delegated stake


