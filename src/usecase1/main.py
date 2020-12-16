import networkx as nx
import random as rand
import argparse
import json
from topology import Topology
from application import Application
from my_as_graph_gen import my_random_internet_as_graph
from my_as_graph_gen import MY_as_graph_gen
from uc1_application import Uc1_application
from uc1_placement import Uc1_placement
from selection import First_ShortestPath
from yafs.core import Sim


def main(data):

    rand.seed(data.seed)  # has to be an object.
    """
    TOPOLOGY creation
    """
    t = Topology()
    AS_graph = my_random_internet_as_graph(data.nb_regions, data.nb_core_nodes_per_region, data.nb_core_nodes_per_region_variance, data.nb_gw_per_region, data.nb_gw_per_region_variance, data.avg_deg_core_node, data.nb_mm, data.nb_mm_variance, data.t_connection_probability, data.seed)
    t.G = AS_graph.G
    t.add_as_graph_link(AS_graph)
    nx.write_gexf(t.G, data.outFILE + '.gexf')

    """
    Application
    """
    app = Uc1_application("UseCase1", t)

    placement = Uc1_placement(name="UseCase1") #Inizializes when starting s
    selectorPath = First_ShortestPath("NR_DECOMP_m")

    s = Sim(t)
    s.deploy_app(app.app, placement, selectorPath)
    s.run(5000,show_progress_monitor=False)

def check_bigger_than_zero(value):
    ival = int(value)
    if ival < 1:
        raise argparse.ArgumentTypeError("Has to be greater than 0")
    return ival

def check_positive_and_zero(value):
    ival = int(value)
    if ival < 0:
        raise argparse.ArgumentTypeError("Has to be positive!")
    return ival

def get_and_check_args(data):
    parser.add_argument("outFILE",
                        type=str,
                        help="output file name for generated graph")
    parser.add_argument("nb_regions", type=check_bigger_than_zero,
                        help="Number of regions")
    parser.add_argument("nb_core_nodes_per_region", type=check_bigger_than_zero, help="Number of core nodes per region")
    parser.add_argument("nb_core_nodes_per_region_variance", type=check_positive_and_zero, help="Variance for number of core nodes per region")
    parser.add_argument("nb_gw_per_region", type=check_positive_and_zero, help="Number of gateways per region")
    parser.add_argument("nb_gw_per_region_variance", type=check_positive_and_zero, help="Number of gateways per region variance")
    parser.add_argument("avg_deg_core_node", type=check_bigger_than_zero, help="average degree of a core node, Pick a random integer with uniform probability.")
    parser.add_argument("nb_mm", type=check_positive_and_zero, help="Number of measuring modules")
    parser.add_argument("nb_mm_variance", type=check_positive_and_zero, help="variance for normal distribution for number of measuring modules")
    parser.add_argument("t_connection_probability", type=check_positive_and_zero, help="probability of m connections to T nodes")
    parser.add_argument("seed", type=check_positive_and_zero, help="set seed for random values")

    x = list(data.values())
    arguments = parser.parse_args(x)

    # Ovisnosti medu argumentima
    if arguments.nb_gw_per_region + arguments.nb_gw_per_region_variance * 3 > arguments.nb_core_nodes_per_region + arguments.nb_core_nodes_per_region_variance * 3:
        raise argparse.ArgumentTypeError("Please make sure that max possible number of gateways (considering 3sigma normal distribution with a variance) be less than a total nb_core_nodes! ")
    return arguments


parser = argparse.ArgumentParser()

if __name__ == '__main__':
    data = json.load(open('topostuff.json'))
    args = get_and_check_args(data)
    main(args)


