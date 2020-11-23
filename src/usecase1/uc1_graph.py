import networkx as nx
from random import randint
import random as rand
from math import floor
import matplotlib.pyplot as plt

class Uc1_graph(object):

    # CONSTANTS ( Shortcuts -> DC = Data Center, NR = router (Network Center), GW = gateway, MM = measuring module )
    # NODES - use case1
    DC_NODE_IPT = 10000
    NR_NODE_IPT = 500
    GW_NODE_IPT = 20
    MM_NODE_IPT = 1

    DC_NODE_RAM = 1000
    NR_NODE_RAM = 60 #TODO this parameter is weird
    GW_NODE_RAM = 100
    MM_NODE_RAM = 1

    # EDGES - use case1
    #mBits
    GW_BW = 10
    NR_BW = 1000
    DC_BW = 100000

    GW_PR = 2
    NR_PR = 2
    DC_PR = 2
    MM_PR = 2

    #TYPES
    DC = "DC"
    NR = "NR"
    GW = "GW"
    MM = "MM"

    #LoRaWAN Data Rate to BW and Propagation Time attributes table
    #Spreading factor is used to determin the package loss.
    # TODO: BW is Mb/s and this is in b/s
    LoRaWAN_databit_translation = {0: (250, 12), 1: (440, 11), 2: (980, 10), 3: (1760, 9),
                                   4: (3125, 8), 5: (5470, 7), 6: (11000, 7)}

    def __init__(self, core_node_count, gw_node_count, method, star_node_count, variance, seed, shared_star_nodes_percentage=0):
        self.core_node_count = core_node_count
        self.gw_node_count = gw_node_count
        self.method = method
        self.start_node_count = star_node_count
        self.variance = variance
        self.shared_star_nodes_percentage = shared_star_nodes_percentage
        self.seed = seed
        self.gateways_index = set()
        rand.seed(seed)

        self.__UC1_graph_generation(core_node_count, gw_node_count, method, star_node_count, variance, seed)

        self.G = nx.Graph()
        self.nb_GW = 0
        self.nb_NR = 0
        self.gw_start_index = 0
        self.gw_end_index = 0
        self.nr_start_index = 0
        self.nr_end_index = 0

    def next(self):
        None,

    def __UC1_graph_generation(self, core_node_count, gw_node_count, method, star_node_count, variance, seed):

        if method == "mymethod":
            a = 0
            #self.__centralPartGen(int(nb_gw), int(nb_nr))
            #self.__starPartGen(int(nb_star_nodes), int(star_nodes_variance), int(max_shared_nodes_percentage))

        if method == "newman-watts-strogatz":
            self.G = nx.newman_watts_strogatz_graph(core_node_count, randint(0, core_node_count-1), 0.1, seed)

        if method == "barabasi-albert":
            self.G = nx.barabasi_albert_graph(core_node_count, randint(1, core_node_count-1), seed)

        if method == "erdos-renyi":
            self.G = nx.erdos_renyi_graph(core_node_count, rand.random(), seed)

        if method == "euclidean":
            dimensions = 2
            self.G = nx.random_geometric_graph(core_node_count, dimensions * rand.random(), dim=dimensions, seed=seed)

        self.__pick_random_GW_nodes(core_node_count, gw_node_count)
        self.__add_star_nodes(star_node_count, variance)

    def __add_star_nodes(self, star_node_count, variance, shared_star_nodes_percentage=0, datarate=5):

        for gw in self.gateways_index:
            nb_star_nodes_rand = abs(int(floor(rand.normalvariate(star_node_count, variance))))
            G_help = nx.generators.star_graph(nb_star_nodes_rand + 1)

            for edge in G_help.edges:
                G_help.add_edge(edge[0], edge[1], BW=self.LoRaWAN_databit_translation[datarate][0], PR=self.MM_PR)

            self.G = nx.union(self.G, G_help, (None, str(gw) + 's'))

    def __pick_random_GW_nodes(self, core_node_count, gw_node_count):
        used_gw = set()
        while gw_node_count:
            gw_index = randint(0, core_node_count-1)
            while gw_index in used_gw:
                gw_index = randint(0, core_node_count-1)
            used_gw.add(gw_index)
            self.G.add_node(gw_index, role_affinity="GW")
            self.gateways_index.add(gw_index)
            gw_node_count -= 1


    def __starPartGen(self, nb_star_nodes, variance, max_shared_nodes_percentage=0, datarate=0):

        if nb_star_nodes > 0:

            # Create star graphs && add LoRaWAN attributes to it && connect % to neighbour gw-s.
            for count in range(self.nb_GW):

                nb_star_nodes_rand = int(floor(rand.normalvariate(nb_star_nodes, variance)))
                G_help = nx.generators.star_graph(nb_star_nodes_rand + 1) # +1 because index[0] will be contracted to gw.

                # Add attributes
                for edge in G_help.edges:
                    G_help.add_edge(edge[0], edge[1], BW=self.LoRaWAN_databit_translation[datarate][0], PR=self.MM_PR)

                for node in G_help.nodes:
                    G_help.add_node(node, IPT=self.MM_NODE_IPT, RAM=self.MM_NODE_RAM, type=self.MM)

                # Add star topology to main graph
                self.G = nx.union(self.G, G_help, (None, str(count) + 'b-'))

                # set shared star nodes among GW.
                # Assumption is that GW ID-s correspond to closeness of GWs in real world. So node 6 is neighbour to 5 and 7
                # so nodes in star topology who's root node is id's 6 can connect to nodes 5 and 7,
                nb_shared_nodes = randint(0, floor((nb_star_nodes_rand) * (max_shared_nodes_percentage / 100.)))
                shared_star_index_used = list()
                while nb_shared_nodes > 0:
                    # Pick random MM in star. Do not pic already used one.
                    # Here we are configuring that no star node can be connected to both left and right neighbour
                    shared_star_index = randint(1, nb_star_nodes_rand)
                    while shared_star_index in shared_star_index_used:
                        shared_star_index = randint(1, nb_star_nodes_rand)
                    shared_star_index_used.append(shared_star_index)

                    #pick randomly left or right neighbour (by index)
                    neighnour = randint(0,1)
                    if neighnour:
                        dest_gw_index = (((self.gw_start_index + count) - 1) % self.nb_GW)
                    else:
                        dest_gw_index = (((self.gw_start_index + count) + 1) % self.nb_GW)
                    if dest_gw_index == 0:
                        # TODO: hack! Maybe refactor. For now its good.
                        dest_gw_index = 1

                    self.G.add_edge(dest_gw_index, str(count) + 'b-' + str(shared_star_index), BW=self.LoRaWAN_databit_translation[datarate][0], PR=self.MM_PR)
                    nb_shared_nodes -= 1

            # Link star graphs to GW nodes.
            for count in range(self.nb_GW):
                self.G = nx.algorithms.contracted_nodes(self.G, self.gw_start_index + count, str(count) + 'b-0')

    def __centralPartGen(self, nb_gw, nb_nr):

        # Create Data Center - always only one
        self.G.add_node(0, IPT=self.DC_NODE_IPT, RAM=self.DC_NODE_RAM, type=self.DC)

        # Number of gateways and network routers
        self.nb_GW = nb_gw
        self.nb_NR = nb_nr

        # Make sure no node is left unconnected (disconnected) completely.
        if self.nb_GW > self.nb_NR:
            min_nb_connections = self.nb_GW
        else:
            min_nb_connections = self.nb_NR

        self.gw_start_index = 1
        self.gw_end_index = self.nb_GW
        self.nr_start_index = self.nb_GW + 1
        self.nr_end_index = self.nb_GW + self.nb_NR

        # TODO: Check this, should it be some kind of distribution?
        nb_connections = randint(min_nb_connections, min_nb_connections * 2)

        # Create gateway and network nodes
        for gw in range(self.nb_GW):
            self.G.add_node(gw + self.gw_start_index, IPT=self.GW_NODE_IPT, RAM=self.GW_NODE_RAM, type=self.GW)
        for nr in range(self.nb_NR):
            self.G.add_node(nr + self.nr_start_index, IPT=self.NR_NODE_IPT, RAM=self.NR_NODE_RAM, type=self.NR)

        # Every NR has a connection to Data Center
        for nr in range(self.nb_NR):
            self.G.add_edge(0, nr + self.nr_start_index, BW=self.DC_BW, PR=self.DC_PR)

        if self.nb_GW > self.nb_NR:
            connected = 0
            # Make lesser ones (nb_NR) have at least 1 degree
            for nr in range(self.nb_NR):
                self.G.add_edge(nr + self.nr_start_index, randint(self.gw_start_index, self.gw_end_index), BW=self.NR_BW, PR=self.NR_PR)
                connected += 1
            # Connect the GW who have degree 0.
            for node, data in self.G.nodes.data():
                if data['type'] == "GW" and self.G.degree[node] == 0:
                    self.G.add_edge(node, randint(self.nr_start_index, self.nr_end_index), BW=self.NR_BW, PR=self.NR_PR)
                    connected += 1

            # Now that every node degree is at least one, randomly pick and place other connections.
            while connected != nb_connections:
                src = randint(self.gw_start_index, self.gw_end_index)
                dest = randint(self.nr_start_index, self.nr_end_index)
                self.G.add_edge(src, dest, BW=self.NR_BW, PR=self.NR_PR)
                connected += 1
        else:
            connected = 0
            # Make lesser ones (nb_NR) have at least 1 degree
            for gw in range(self.nb_GW):
                self.G.add_edge(gw + 1, randint(self.nr_start_index, self.nr_end_index), BW=self.NR_BW, PR=self.NR_PR)
                connected += 1
            # Connect the GW who have degree 0 1st.
            for node, data in self.G.nodes(data="type"):
                # TODO: Check [
                if data == "NR" and self.G.degree[node] == 0:
                    self.G.add_edge(node, randint(self.gw_start_index, self.gw_end_index), BW=self.NR_BW, PR=self.NR_PR)
                    connected += 1

            # Now that every node degree is at least one, randomly pick and place other connections.
            while connected != nb_connections:
                src = randint(self.gw_start_index, self.gw_end_index)
                dest = randint(self.nr_start_index, self.nr_end_index)
                self.G.add_edge(src, dest, BW=self.NR_BW, PR=self.NR_PR)
                connected += 1

        # Connect all NR with each other, it's separated so it can be easily excluded for better topology plot.
        # Reason why we do this is cause all NR can use HTTP/MQTT to communicate to each other and compression
        # algorithm will most likely run only on few NR. So we will have to send some packets from one NR to other NR
        # do compress them.

        for nr_src in range(self.nr_start_index, self.nr_end_index+1):
            for nr_dest in range(self.nr_start_index, self.nr_end_index+1):
                if nr_src == nr_dest:# No self-loops!
                    continue
                self.G.add_edge(nr_src, nr_dest, BW=self.NR_BW, PR=self.NR_PR)

    def __eukRavLogicGraphGen(self, nb_nodes):

        # Create root server
        self.G.add_node(0, {"IPT": self.DC_NODE_IPT, "RAM": self.DC_NODE_RAM})

        self.G = nx.random_geometric_graph(nb_nodes, 0.5)

    def __createCentralPart(self):
        return nx.thresholded_random_geometric_graph()

    def __createEdgePart(num_of_edge_nodes):
        return nx.generators.classic.star_graph(num_of_edge_nodes)

    """
    plt.subplot(121)
    nx.draw(self.G, with_labels=True, font_weight='bold')
    plt.show()
    a = 0
    """



