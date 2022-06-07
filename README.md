# Nym_Mixnet_Econ_Simulator

A simulator for the reward mechanism of the Nym network. 


## File structure and classes

There are seven .py files: 6 classes and a main.py file.

The six classes are: 
- **Config**: contains all the configuration variables of the simulation. 
- **Input_Functions**: contains libraries of pre-determined functions that can be used to model input simulation variables.
- **Node**: each object is a mix node, the class contains the mix node variables of interest.
- **Network**: creates and manages the list of nodes that exist in the network at any time.
- **Econ_Results**: creates and manages the global variables of the system, evolving them over time. The class includes variables that account for the global state of the token supply (how much of it is pledged, delegated, in the mixmining reserve, distributed as rewards, etc.), as well as instantiating and managing a Network object that keeps track of the list of mix nodes over time. 
- **Plot_Results**: contains a variety of functions to generate and save figures displaying variables of interest of a simulation that has just been run in an **Econ_Results** instance. 


## How to run a simulation (basic)

**Step 0**: download the seven .py files to a machine that can run python scripts

**Step 1**: edit the file `Configuration_econ.py` to set the scenario (input variables) that you want to simulate

**Step 2**: run the simulation with the following command: `python3 main.py`

**Step 3**: once the simulation has ended, see the results in the Output directory


## Tinkering with the simulation

In addition to changing parameter values in `Configuration_econ.py` to simulate different secenarios, you can also: 
- comment out calls to Plot_Results in `main.py` to produce fewer graphs; or alternatively, **add** calls in `main.py` to Plot_Results functions in order to produce additional graphs; and it is also possible to add plotting functions to `Plot_Results.py` (and corresponding calls from `main.py`) in order to depict additional results. 
- it is possible to add new input functions of interest to the Input_Functions class 
- it is possible to code more sophisticated token exchange rates, and user fees than in the current version
- the current performance bottleneck is the function `sample_work_share_mixes` in the class Network, with the overhead being proportional to `k` (number of rewarded mix nodes per epoch)


## Author

Claudia Diaz

## License

Apache-2.0

