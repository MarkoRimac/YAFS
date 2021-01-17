import random as rand
import argparse
import json
import networkx as nx
from topology import Topology
from uc1_topology import my_random_internet_as_graph
from uc1_application import Uc1_application
from uc1_placement import Uc1_placement
from uc1_selection import Uc1_First_ShortestPath
from yafs.core import Sim
from uc1_stats import Uc1_stats


def main(data):

    rand.seed(data.seed)  # has to be an object.
    #TOPOLOGY creation
    t = Topology()
    AS_graph = my_random_internet_as_graph(data.nb_regions, data.nb_core_nodes_per_region, data.nb_core_nodes_per_region_variance, data.nb_gw_per_region, data.nb_gw_per_region_variance, data.avg_deg_core_node, data.nb_mm, data.nb_mm_variance, data.t_connection_probability, data.lorawan_datarate, data.seed)
    t.G = AS_graph.G
    t.add_as_graph_link(AS_graph)
    #Application
    app = Uc1_application("UseCase1", data.app_version, t, N=data.N, h=data.h, d=data.d, P=data.P, M=data.M, compressionRatio=data.Cr)

    placement = Uc1_placement(data.filt_placement_method, data.nb_filt_per_region, data.app_version, name="UseCase1")  # Inizializes when starting s

    if data.app_version == "DECOMP_FILT_B" or data.app_version == "DECOMP_GW" or data.app_version == "NONE":
        selectorPath = Uc1_First_ShortestPath("FILT_DP_m") # Message which is to be filtered
    elif data.app_version == "DECOMP_FILT_A" or data.app_version == "DECOMP_DP":
        selectorPath = Uc1_First_ShortestPath("FILT_DECOMP_m")
    else:
        raise exec("Unknown app_version!")

    s = Sim(t)
    s.deploy_app(app.app, placement, selectorPath)
    runtime_time = 5000
    s.run(runtime_time,show_progress_monitor=False)
    stats = Uc1_stats(str(data.config_version), data.app_version, runtime_time)
    stats.uc1_do_stats()
    stats.uc1_stats_save_gexf(t, data.outFILE) # Neki attributi se dodaju u runtimeu, pa zapisi graf tek tu.

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

def check_positive_float(value):
    ival = float(value)
    if ival <= 0:
        raise argparse.ArgumentTypeError("Has to be greater than 0!")
    return ival

def check_app_version(value):
    if value in ["DECOMP_FILT_A", "DECOMP_FILT_B", "NONE", "DECOMP_GW", "DECOMP_DP"]:
        return value
    else:
        raise argparse.ArgumentTypeError("Please pick between: [DECOMP_FILT_A, DECOMP_FILT_B, DECOMP_GW, DECOMP_DP, NONE]")

def check_placement_type(value):
    if value in ["BC", "HIGHEST_DEGREE"]:
        return value
    else:
        raise argparse.ArgumentTypeError("Please pick between: [BC, HIGHEST_DEGREE]")

def check_lorawan_datarate(value):
    ival = int(value)
    if ival < 0 or ival > 6:
        raise argparse.ArgumentTypeError("Has to be 0, 1,2,3,4,5,or6!")
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
    parser.add_argument("nb_filt_per_region", type=check_bigger_than_zero, help="number of nr filt modules per region")
    parser.add_argument("avg_deg_core_node", type=check_bigger_than_zero, help="average degree of a core node, Pick a random integer with uniform probability.")
    parser.add_argument("nb_mm", type=check_positive_and_zero, help="Number of measuring modules")
    parser.add_argument("nb_mm_variance", type=check_positive_and_zero, help="variance for normal distribution for number of measuring modules")
    parser.add_argument("t_connection_probability", type=check_positive_and_zero, help="probability of m connections to T nodes")
    parser.add_argument("lorawan_datarate", type=check_lorawan_datarate, help="check table for lorwan")
    parser.add_argument("seed", type=check_positive_and_zero, help="set seed for random values")
    parser.add_argument("N", type=check_positive_and_zero, help="number of instruction multiplier")
    parser.add_argument("h", type=check_positive_and_zero, help="instruction header multiplier")
    parser.add_argument("d", type=check_positive_and_zero, help="instruction data multiplier")
    parser.add_argument("P", type=check_positive_and_zero, help="multiplier for processing power in all nodes and memory in NR and GW")
    parser.add_argument("M", type=check_positive_and_zero, help="multiplier for memory in MM and GW")
    parser.add_argument("Cr", type=check_positive_float, help="compression ratio")
    parser.add_argument("app_version", type=check_app_version, help="DECOMP_FILT, FILT_DECOMP or NONE types of applications. DECOMP_FILT means that message is decompressed first then filtered, and so on..")
    parser.add_argument("filt_placement_method", type=check_placement_type, help="PICK BETWEEN BC or HIGHEST_DEGREE")
    parser.add_argument("config_version", type=str, help="set version of config. It makes sures not to overwrite privious config output files in slike folder")

    x = list(data.values())
    arguments = parser.parse_args(x)

    # Ovisnosti medu argumentima
    if arguments.nb_gw_per_region + arguments.nb_gw_per_region_variance * 3 > arguments.nb_core_nodes_per_region + arguments.nb_core_nodes_per_region_variance * 3:
        raise argparse.ArgumentTypeError("Please make sure that max possible number of gateways (considering 3sigma normal distribution with a variance) be less than a total nb_core_nodes! ")

    if arguments.nb_filt_per_region * arguments.nb_regions > (arguments.nb_core_nodes_per_region + arguments.nb_core_nodes_per_region_variance * 3) - (arguments.nb_gw_per_region + arguments.nb_gw_per_region_variance * 3):
        raise argparse.ArgumentTypeError("Not enough free core nodes for that amount of FILT modules in region!")

    return arguments

parser = argparse.ArgumentParser()

if __name__ == '__main__':
    data = json.load(open('config.json'))
    args = get_and_check_args(data)
    mm = 1
    filt_per_reg = 3
    for _ in range(3):
        mm = mm + 2
        filt_per_reg = 3
        for l in range (3):
            filt_per_reg = filt_per_reg + 3
            args.nb_filt_per_region = filt_per_reg
            args.nb_mm = mm
            main(args)
        f = open("table.txt", "a")
        f.write('\n')
        f.close()


