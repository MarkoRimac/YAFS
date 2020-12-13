"""
    This type of algorithm have two obligatory functions:

        *initial_allocation*: invoked at the start of the simulation

        *run* invoked according to the assigned temporal distribution.

"""

from yafs.placement import Placement
import networkx as nx
import random as rand

class Uc1_placement(Placement):

    def __init__(self, **kwargs):
        super(Uc1_placement,self).__init__(**kwargs)
        self.T_nodes_ids = list()
        self.M_nodes_ids = list()
        self.MM_nodes_ids = list()
        self.GW_nodes_ids = list()
        self.NR_nodes_ids = list()

        # konstante
        self.has_compression = True


    def initial_allocation(self, sim, app_name):
        app = sim.apps[app_name]
        topology = sim.topology
        services = app.services
        id_and_type = nx.get_node_attributes(topology.G, "type")
        data = app.data

        for id, type in id_and_type.items():
            if type == "MM":
                self.MM_nodes_ids.append(id)
                for x in data:
                    for m in x:
                        if m == "MM":
                            topology.G.add_node(id, IPT=x[m]['IPT'], RAM=x[m]['RAM'])
            elif type == "GW":
                self.GW_nodes_ids.append(id)
                for x in data:
                    for m in x:
                        if m == "GW":
                            topology.G.add_node(id, IPT=x[m]['IPT'], RAM=x[m]['RAM'])
            elif type == "T":
                self.T_nodes_ids.append(id)
                for x in data:
                    for m in x:
                        if m == "DC":
                            topology.G.add_node(id, IPT=x[m]['IPT'], RAM=x[m]['RAM'])
            elif type == "M":
                self.M_nodes_ids.append(id)
                for x in data:
                    for m in x:
                        if m == "NR":
                            topology.G.add_node(id, IPT=x[m]['IPT'], RAM=x[m]['RAM'])

        sim.deploy_module(app.name, "GW", services["GW"], self.GW_nodes_ids)
        sim.deploy_module(app.name, "MM", services["MM"], self.MM_nodes_ids) # SOURCE
        DC_nodes = list()
        DC_nodes.append(rand.choice(self.T_nodes_ids))
        sim.deploy_module(app.name, "DC", services["DC"], DC_nodes) # SOURCE
        # MARKO: POPULATION -> Random T node as DC sink
        #sim.deploy_sink(app.name, DC_nodes[0], "DC")

        # MARKO: PLACEMENT
        # Node with biggest degree in a region
        taken_nodes = list()
        for region in topology.my_as_graph.regions.keys():
            nodes = topology.my_as_graph.regions[region].intersection(self.M_nodes_ids)
            result = sorted(topology.G.degree(nodes), key=lambda x: x[1], reverse=True)
            if result[0][0] in taken_nodes: # MARKO: Ovaj NR cvor se nalazi u vise regija. Stoga necemo dodavati novi NR na taj cvor! Taj NR cvor ce sluziti dvije regije
                continue
            taken_nodes.append(result[0][0])
            NR_nodes = list()
            NR_nodes.append(result[0][0]) # MARKO: Za sada samo jedan NR cvor po regiji
            taken_nodes.append(result[0][0])
            sim.deploy_module(app.name, "NR", services["NR"], NR_nodes)


