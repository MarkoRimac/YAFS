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

    def initial_allocation(self, sim, app_name):
        app = sim.apps[app_name]
        topology = sim.topology
        services = app.services
        id_and_type = nx.get_node_attributes(topology.G, "type")

        # nadi ID covore od pjedinih tipova.
        for id, type in id_and_type.items():
            if type == "MM":
                self.MM_nodes_ids.append(id)
                self.__link_module_attribute_with_topology_nodes("MM", self.MM_nodes_ids, topology, app) # Linkaj attribute iz uc1_app u fizicki cvor. tj. node_id
            elif type == "GW":
                self.GW_nodes_ids.append(id)
                self.__link_module_attribute_with_topology_nodes("GW", self.GW_nodes_ids, topology, app)
            elif type == "T":
                self.T_nodes_ids.append(id)
            elif type == "M":
                self.M_nodes_ids.append(id)
                #  attributi ce biti dodani kasnije na placementu za NR cvor.

        """ POPULATION! + PLACEMENT"""

        sim.deploy_module(app.name, "MM", services["MM"], self.MM_nodes_ids)    # Definiranje sourca preko servisa, a ne preko "pure source". Zašto? Bezveze, moglo se i s ovim dolje, posto je taj modul samo i samo source!
        ## distribution = DeterministicDistribution_mm_uc1  # Ovo je drugi nacin na koji se moze deplioyati soruce kao "pure source" modul.
        ## sim.deploy_source(app_name, MM_nodes_ids, message=add_source_messages("MM"),distribution) #

        DC_id = rand.choice(self.T_nodes_ids)  # Random DC cvor na T cvoru
        self.__link_module_attribute_with_topology_nodes("DC",[DC_id], topology, app)
        sim.deploy_module(app.name, "DC", services["DC"], [DC_id]) #  Definiranje SINKA preko DC servisa!

        """END OF POPULATION"""

        """ PLACEMENT """
        sim.deploy_module(app.name, "GW", services["GW"], self.GW_nodes_ids)
        # Node with biggest degree in a region
        taken_nodes = list()    # Buduci da cvor moze biti u vise regija, ajmo za sada uzeti da je NR-ova onoliko koliko je i regija.
        for region in topology.my_as_graph.regions.keys():

            nodes = topology.my_as_graph.regions[region].intersection(self.M_nodes_ids)
            result = sorted(topology.G.degree(nodes), key=lambda x: x[1], reverse=True)

            for index in range(len(result)):
                if result[index][0] in taken_nodes:
                    continue  # Trazi sljedeci highest degree node u toj regiji, jer je ovaj prvi vec zauzet!
                taken_nodes.append(result[index][0])
                sim.deploy_module(app.name, "NR", services["NR"], [result[index][0]])
                sim.deploy_sink(app.name, result[index][0], "NR_SINK") #  Dodaj DES process za sink!
                self.__link_module_attribute_with_topology_nodes("NR", [result[index][0]], topology, app)
                break

    def __link_module_attribute_with_topology_nodes(self, module, node_ids,topology, app):
        data = app.data
        for node_id in node_ids:
            for x in data:
                for m in x:
                    if m == module:
                        topology.G.add_node(node_id, IPT=x[m]['IPT'], RAM=x[m]['RAM'])

