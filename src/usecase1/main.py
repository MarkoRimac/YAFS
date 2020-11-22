import sys
from CreateGraph import CreateGraph
import matplotlib.pyplot as plt
import networkx as nx

def main(argv):
    """
    TOPOLOGY creation
    """

    myGraph = CreateGraph()
    # seed, nb_gw, nb_nodes, nb_star_nodes, variance, max_stared_nodes_percentage, method
    myGraph.UC1_graph_generation(argv[0], argv[1], argv[2], argv[3], argv[4], argv[5])

    nx.write_gexf(myGraph.G, "out.gexf")
"""
    plt.subplot(121)
    nx.draw(myGraph.G, with_labels=True, font_weight='bold')
    plt.show()
    """

if __name__ == '__main__':
    if len(sys.argv) < 7:
        print("Some argments are missing!")
        sys.exit(1)
    elif len(sys.argv) > 7:
        print("Too many arguments!")
        sys.exit(1)
    else:
        main(sys.argv[1:])


