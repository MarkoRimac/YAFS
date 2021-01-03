"""
    This type of algorithm have two obligatory functions:

        *initial_allocation*: invoked at the start of the simulation

        *run* invoked according to the assigned temporal distribution.

"""

from yafs.placement import Placement
import networkx as nx
import random as rand

class Uc1_placement(Placement):

    def __init__(self, nr_filt_placement_method, nb_nr_filt_per_region, app_version, curr_position=0, **kwargs):
        super(Uc1_placement,self).__init__(**kwargs)
        self.nr_filt_placement_method = nr_filt_placement_method
        self.nb_nr_filt_per_region = nb_nr_filt_per_region
        self.app_version = app_version
        self.T_nodes_ids = list()
        self.M_nodes_ids = list()
        self.MM_nodes_ids = list()
        self.GW_nodes_ids = list()
        self.NR_FILT_nodes_ids = list()
        self.NR_DECOM_nodes_ids = list()
        self.DP_nodes_ids = list()
        self.DC_nodes_ids = list()
        self.curr_position = curr_position

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
                self.__link_module_attribute_with_topology_nodes("GW", self.GW_nodes_ids, topology, app) # oni su preodređenii već u definiciji topologije kroz "CP" cvorove.
            elif type == "T":
                self.T_nodes_ids.append(id)
                self.__link_module_attribute_with_topology_nodes("NR_FILT", self.T_nodes_ids, topology, app)  # neka svi ostali cvorovi imaju atribute kao NR
            elif type == "M":
                self.M_nodes_ids.append(id)
                self.__link_module_attribute_with_topology_nodes("NR_FILT", self.M_nodes_ids, topology, app)  # neka svi ostali cvorovi imaju atribute kao NR
                #  attributi ce biti dodani kasnije na placementu za NR cvor.

        """ POPULATION! + PLACEMENT"""

        self.__MM_placement(sim, topology, services, app)
        self.__DC_STORAGE_placement(sim, topology, services, app)
        self.__DP_placement(sim, topology, services, app)
        self.__GW_placement(sim, topology, services, app)
        self.__NR_FILT_placement(sim, topology, services, app)
        self.__NR_DECOMP_placement(sim, topology, services, app)

    def __NR_DECOMP_placement(self, sim, topology, services, app):
        if self.app_version == "DECOMP_NR_A" or self.app_version == "DECOMP_NR_B":
            for index in self.NR_FILT_nodes_ids:
                self.NR_DECOM_nodes_ids.append(index)
                id_DES = sim.deploy_module(app.name, "NR_DECOMP", services["NR_DECOMP"], [index])
                updated_id_DES = topology.G.nodes[index]['id_DES'] + ' ' + str(id_DES[0])
                if self.app_version == "DECOMP_NR_A":
                    topology.G.add_node(index, type="NR_FILT_DECOMP", id_DES=updated_id_DES)
                else:
                    topology.G.add_node(index, type="NR_DECOMP_FILT", id_DES=updated_id_DES)
        if self.app_version == "DECOMP_GW":
            for index in self.GW_nodes_ids:
                self.NR_DECOM_nodes_ids.append(index)
                id_DES = sim.deploy_module(app.name, "NR_DECOMP", services["NR_DECOMP"], [index])
                updated_id_DES = topology.G.nodes[index]['id_DES'] + ' ' + str(id_DES[0])
                topology.G.add_node(index, type="GW_DECOMP", id_DES=updated_id_DES)
        if self.app_version == "DECOMP_DP":
            for index in self.DP_nodes_ids:
                self.NR_DECOM_nodes_ids.append(index)
                id_DES = sim.deploy_module(app.name, "NR_DECOMP", services["NR_DECOMP"], [index])
                updated_id_DES = topology.G.nodes[index]['id_DES'] + ' ' + str(id_DES[0])
                topology.G.add_node(index, type="DECOMP_DP", id_DES=updated_id_DES)
        if self.app_version == "DECOMP_ALONE":
            self.NR_DECOM_nodes_ids.append(self.curr_position)
            id_DES = sim.deploy_module(app.name, "NR_DECOMP", services["NR_DECOMP"], [self.curr_position])
            self.__link_module_attribute_with_topology_nodes("NR_DECOMP", [self.curr_position], topology, app)
            topology.G.add_node(self.curr_position, type="DECOMP_ALONE", id_DES=str(id_DES))

    def __NR_FILT_placement(self, sim, topology, services, app):

        if self.nr_filt_placement_method == "HIGHEST_DEGREE":
            self.__highest_degree_nr_filt_placement(sim, topology, services, app)
        elif self.nr_filt_placement_method == "BC":
            self.__bc_nr_filt_placement(sim, topology, services, app)
        else:
            raise exec("nr_filt placement method is not supported!")

    def __GW_placement(self, sim, topology, services, app):
        id_DES = sim.deploy_module(app.name, "GW", services["GW"], self.GW_nodes_ids)
        index = 0
        for node in self.GW_nodes_ids:
            topology.G.add_node(node, id_DES=str(id_DES[index]))
            index = index + 1

    def __MM_placement(self, sim, topology, services, app):
        id_DES = sim.deploy_module(app.name, "MM", services["MM"], self.MM_nodes_ids)    # Definiranje sourca preko servisa, a ne preko "pure source". Zašto? Bezveze, moglo se i s ovim dolje, posto je taj modul samo i samo source!
        ## distribution = DeterministicDistribution_mm_uc1  # Ovo je drugi nacin na koji se moze deplioyati soruce kao "pure source" modul.
        ## sim.deploy_source(app_name, MM_nodes_ids, message=add_source_messages("MM"),distribution)
        index = 0
        for node in self.MM_nodes_ids:
            topology.G.add_node(node, id_DES=id_DES[index])
            index = index + 1

    def __DC_STORAGE_placement(self, sim, topology, services, app):
        # Stavi DC_STORAGE na random T cvor
        self.DC_id = rand.choice(self.T_nodes_ids)
        self.DC_nodes_ids.append(self.DC_id)
        self.__link_module_attribute_with_topology_nodes("DC_STORAGE",[self.DC_id], topology, app)
        id_DES1 = sim.deploy_module(app.name, "DC_STORAGE", services["DC_STORAGE"], [self.DC_id]) #  Definiranje SINKA preko DC servisa!
        topology.G.add_node(self.DC_id, type="DC_STORAGE", id_DES=str(id_DES1[0]))


    def __DP_placement(self, sim, topology, services, app):

        #  highest_degree_T_node
        nodes = set(self.T_nodes_ids).difference(self.DC_nodes_ids)
        result = sorted(topology.G.degree(nodes), key=lambda x: x[1], reverse=True)
        # TODO: extend tako da prima vise DP na T cvorove i cak i na M cvorove!
        self.DP_nodes_ids.append(result[0][0])
        id_DES = sim.deploy_module(app.name, "DC_PROC", services["DC_PROC"], [result[0][0]])
        topology.G.add_node(result[0][0], type="DC_PROC", id_DES=str(id_DES[0]))
        self.__link_module_attribute_with_topology_nodes("DC_PROC", [result[0][0]], topology, app)

    def __link_module_attribute_with_topology_nodes(self, module, node_ids,topology, app):
        data = app.data
        for node_id in node_ids:
            for x in data:
                for m in x:
                    if m == module:
                        topology.G.add_node(node_id, IPT=x[m]['IPT'], RAM=x[m]['RAM'])


    def __highest_degree_nr_filt_placement(self, sim, topology, services, app):
        taken_nodes = list() # sprjecava da na dva ista cvora bude NR filt za dvije regije.
        for region in topology.my_as_graph.regions.keys():

            nodes = topology.my_as_graph.regions[region].intersection(self.M_nodes_ids).difference(taken_nodes)
            result = topology.G.degree(nodes)
            result = sorted(result , key=lambda x: x[1], reverse=True)

            for _ in range(self.nb_nr_filt_per_region):
                taken_nodes.append(result[0][0])
                id_DES = sim.deploy_module(app.name, "NR_FILT", services["NR_FILT"], [result[0][0]])
                topology.G.add_node(result[0][0], regions=region, type="NR_FILT", id_DES=str(id_DES[0]))  # Daj tom NR_FILT atribut kao da je u jednoj regiji, da kasnije u selectino methodu neki MM iz jedne refgije preko shortest patha ne odaberu neki drugi NR iz druge regije zato sto im je blizi.
                sim.deploy_sink(app.name, result[0][0], "NR_SINK") #  Dodaj sink! On nema DES PROCES!
                self.__link_module_attribute_with_topology_nodes("NR_FILT", [result[0][0]], topology, app)
                self.NR_FILT_nodes_ids.append(result[0][0])
                result.remove(result[0])

    def __bc_nr_filt_placement(self, sim, topology, services, app):
        taken_nodes = list() # sprjecava da na dva ista cvora bude NR filt za dvije regije.
        for region in sim.topology.my_as_graph.regions:

            # BC izmedu svih GW cvorova u toj regiji!
            nodes_src = sim.topology.my_as_graph.nodes["GW"].intersection(sim.topology.my_as_graph.regions[region]).difference(taken_nodes)
            result = nx.betweenness_centrality_subset(sim.topology.G, nodes_src, nodes_src)
            result = list(result.items())
            result = sorted(result, key=lambda x: float(x[1]), reverse=True)

            for _ in range(self.nb_nr_filt_per_region):
                while topology.G.nodes[result[0][0]]['type'] != "M":
                    result.remove(result[0]) # Trazi slobodni M CVOR!
                    # sanity check: Nece nikada ne naci M cvor zato sto je to osigurano preko input parametar sanity provjera.

                taken_nodes.append(result[0][0])
                id_DES = sim.deploy_module(app.name, "NR_FILT", services["NR_FILT"], [result[0][0]])
                topology.G.add_node(result[0][0], regions=region, type="NR_FILT", id_DES=str(id_DES[0]))  # Daj tom NR_FILT atribut kao da je u jednoj regiji, da kasnije u selectino methodu neki MM iz jedne refgije preko shortest patha ne odaberu neki drugi NR iz druge regije zato sto im je blizi.
                sim.deploy_sink(app.name, result[0][0], "NR_SINK") #  Dodaj sink! On nema DES PROCES!
                self.__link_module_attribute_with_topology_nodes("NR_FILT", [result[0][0]], topology, app)
                self.NR_FILT_nodes_ids.append(result[0][0])
                result.remove(result[0])