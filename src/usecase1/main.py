import sys
from CreateGraph import CreateGraph
import matplotlib.pyplot as plt
import networkx as nx
import argparse

def main(args):
    """
    TOPOLOGY creation
    """

    print(args.method, args.gw_node_count)
    myGraph = CreateGraph()
    # seed, nb_gw, nb_nodes, nb_star_nodes, variance, max_stared_nodes_percentage, method
    myGraph.UC1_graph_generation(argv[0], argv[1], argv[2], argv[3], argv[4], argv[5])

    nx.write_gexf(myGraph.G, args.method)

    plt.subplot(121)
    nx.draw(myGraph.G, with_labels=True, font_weight='bold')
    plt.show()

def check_bigger_than_three(value):
    ival = int(value)
    if ival < 3:
        raise argparse.ArgumentTypeError("Number of nodes in core part has to be at least 3." +
                                         "That is, it has to be one DC one NR and one GW")
    return ival

def check_bigger_than_one(value):
    ival = int(value)
    if ival < 1:
        raise argparse.ArgumentTypeError("Number of GW nodes has to be greater than 1")
    return ival

def check_possible_methods(method):
    if method not in core_graph_methods:
        raise argparse.ArgumentTypeError("Not valid method! Valid methods are: " + str(core_graph_methods))
    return method

def get_and_check_args():
    parser.add_argument("outFILE",
                        type=str,
                        help="output file name for generated graph")
    parser.add_argument("core_node_count", type=check_bigger_than_three,
                              help="Number of nodes in core part of topology")
    parser.add_argument("gw_node_count", type=check_bigger_than_one, help="Number of GW nodes")
    parser.add_argument("method", type=check_possible_methods, help="Name of method used to generate core function")

    args = parser.parse_args()

    # Post parser conditions. Conditions between args checked.
    if args.gw_node_count > args.core_node_count - 2:
        raise argparse.ArgumentTypeError("Please make sure that: nb_gw <= nb_core_nodes - 2"
                                         "always have to exist ")
    return args


parser = argparse.ArgumentParser()
core_graph_methods = ("marko", "janko")

if __name__ == '__main__':
    args = get_and_check_args()
    main(args)


