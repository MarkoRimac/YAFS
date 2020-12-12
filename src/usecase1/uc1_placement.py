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
        for id, type in id_and_type.items():
            if type == "MM":
                self.MM_nodes_ids.append(id)
            elif type == "GW":
                for module in app.data:
                    for key in module:
                        if key == 'GW': #tu se da jos definirati ima li ili ne kompresiju.
                            if self.has_compression:
                                module["gws_with_compression"].append(id) # Dodaj attribut da ima compresiju
                            self.GW_nodes_ids.append(id)
            elif type == "T":
                self.T_nodes_ids.append(id)
            elif type == "M":
                self.M_nodes_ids.append(id)

        sim.deploy_module(app.name, "GW", services["GW"], self.GW_nodes_ids)
        sim.deploy_module(app.name, "MM", services["MM"], self.MM_nodes_ids)
        # MARKO: POPULATION -> Random T node as DC sink
        sim.deploy_sink(app.name, "DC", list(rand.choice(self.T_nodes_ids)))

        # MARKO: PLACEMENT
        # Node with biggest degree in a region
        for region in topology.my_as_graph.regions.keys():
            nodes = topology.my_as_graph.regions[region].intersection(self.M_nodes_ids)
            sorted(nodes.degree, reverse=True)
            sim.deploy_module(app.name, "NR", services["NR"], list(nodes[0]))

    def testing(self, sim, app, topology):

        services = app.services
        id_and_type = nx.get_node_attributes(topology.G, "type")
        for id, type in id_and_type.items():
            if type == "MM":
                self.MM_nodes_ids.append(id)
            elif type == "GW":
                self.GW_nodes_ids.append(id)
            elif type == "T":
                self.T_nodes_ids.append(id)
            elif type == "M":
                self.M_nodes_ids.append(id)

        sim.deploy_module(app.name, "GW", services["GW"], self.GW_nodes_ids)
        sim.deploy_module(app.name, "MM", services["MM"], self.MM_nodes_ids)
        # MARKO: POPULATION -> Random T node as DC sink
        sim.deploy_sink(app.name, list(rand.choice(self.T_nodes_ids), "DC"))

        # Node with biggest degree in a region
        for region in topology.my_as_graph.regions.keys():
            nodes = topology.my_as_graph.regions[region].intersection(self.M_nodes_ids)
            sorted(nodes.degree, reverse=True)
            for module in app.data:
                for key in module:
                    if key == 'NR':  # tu se da jos definirati ima li ili ne kompresiju.
                        if self.has_compression:
                            module["decompression_after"].append(nodes[0])  # Dodaj attribut da ima compresiju
            sim.deploy_module(app.name, "NR", services["NR"], list(nodes[0]))




