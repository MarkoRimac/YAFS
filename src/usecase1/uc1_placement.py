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
                self.__link_module_attribute_with_topology_nodes("NR", self.GW_nodes_ids, topology, app)  # neka svi ostali cvorovi imaju atribute kao NR
            elif type == "M":
                self.M_nodes_ids.append(id)
                self.__link_module_attribute_with_topology_nodes("NR", self.GW_nodes_ids, topology, app)  # neka svi ostali cvorovi imaju atribute kao NR
                #  attributi ce biti dodani kasnije na placementu za NR cvor.

        """ POPULATION! + PLACEMENT"""

        id_DES = sim.deploy_module(app.name, "MM", services["MM"], self.MM_nodes_ids)    # Definiranje sourca preko servisa, a ne preko "pure source". Zašto? Bezveze, moglo se i s ovim dolje, posto je taj modul samo i samo source!
        ## distribution = DeterministicDistribution_mm_uc1  # Ovo je drugi nacin na koji se moze deplioyati soruce kao "pure source" modul.
        ## sim.deploy_source(app_name, MM_nodes_ids, message=add_source_messages("MM"),distribution) #
        index = 0
        for node in self.MM_nodes_ids:
            topology.G.add_node(node, id_DES=id_DES[index])
            index = index + 1

        DC_id = rand.choice(self.T_nodes_ids)  # Random DC cvor na T cvoru
        self.__link_module_attribute_with_topology_nodes("DC_PROC",[DC_id], topology, app)
        self.__link_module_attribute_with_topology_nodes("DC_STORAGE",[DC_id], topology, app)
        id_DES1 = sim.deploy_module(app.name, "DC_PROC", services["DC_PROC"], [DC_id]) #  Definiranje SINKA preko DC servisa!
        id_DES2 = sim.deploy_module(app.name, "DC_STORAGE", services["DC_STORAGE"], [DC_id]) #  Definiranje SINKA preko DC servisa!
        topology.G.add_node(DC_id, id_DES=str(id_DES1[0]) + ',' + str(id_DES2[0])) # Dva DES procesa na cvoru.

        """END OF POPULATION"""

        """ PLACEMENT """
        id_DES = sim.deploy_module(app.name, "GW", services["GW"], self.GW_nodes_ids)

        #  DODAJ id_DES attribut.
        index = 0
        for node in self.GW_nodes_ids:
            topology.G.add_node(node, id_DES=id_DES[index])
            index = index + 1

        # Node with biggest degree in a region
        taken_nodes = list()    # Buduci da cvor moze biti u vise regija, ajmo za sada uzeti da je NR-ova onoliko koliko je i regija.
        for region in topology.my_as_graph.regions.keys():

            nodes = topology.my_as_graph.regions[region].intersection(self.M_nodes_ids)
            result = sorted(topology.G.degree(nodes), key=lambda x: x[1], reverse=True)

            for index in range(len(result)):
                if result[index][0] in taken_nodes:
                    continue  # Trazi sljedeci highest degree node u toj regiji, jer je ovaj prvi vec zauzet!
                taken_nodes.append(result[index][0])
                id_DES1 = sim.deploy_module(app.name, "NR_FILT", services["NR_FILT"], [result[index][0]])
                id_DES2 = sim.deploy_module(app.name, "NR_DECOMP", services["NR_DECOMP"], [result[index][0]])
                topology.G.add_node(result[index][0], regions=region, type="NR", id_DES=str(id_DES1[0]) + ',' + str(id_DES2[0]))  # Dva DES procesa na cvoru.
                sim.deploy_sink(app.name, result[index][0], "NR_SINK") #  Dodaj sink! On nema DES PROCES!
                self.__link_module_attribute_with_topology_nodes("NR_FILT", [result[index][0]], topology, app)
                self.__link_module_attribute_with_topology_nodes("NR_DECOMP", [result[index][0]], topology, app)
                break

    def __link_module_attribute_with_topology_nodes(self, module, node_ids,topology, app):
        data = app.data
        for node_id in node_ids:
            for x in data:
                for m in x:
                    if m == module:
                        topology.G.add_node(node_id, IPT=x[m]['IPT'], RAM=x[m]['RAM'])

