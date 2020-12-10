"""
    This type of algorithm have two obligatory functions:

        *initial_allocation*: invoked at the start of the simulation

        *run* invoked according to the assigned temporal distribution.

"""

from yafs.placement import Placement
import networkx as nx
import random as rand

class Uc1_placement(Placement):

    def initial_allocation(self, sim, app_name):
        #We find the ID-nodo/resource
        kind = {type: "MM"} # or whatever tag

        id_cluster = sim.topology.find_IDs(kind)
        app = sim.apps[app_name]
        services = app.services

        for module in services:
            if module in self.scaleServices:
                for rep in range(0, self.scaleServices[module]):
                    idDES = sim.deploy_module(app_name,module,services[module],id_cluster)


    def testing(self, sim, topology, app_name):

        app = sim.apps[app_name]
        services = app.services
        T_nodes_ids = list()
        M_nodes_ids = list()

        id_and_type = nx.get_node_attributes(topology.G, "type")
        for id, type in id_and_type.items():
            if type == "MM":
                sim.deploy_module(app, "MM", services["MM"], id)
            elif type == "GW":
                sim.deploy_module(app, "GW", services["GW"], id)
            elif type == "T":
                T_nodes_ids.append(id)
            elif type == "M":
                M_nodes_ids.append(id)

        # Random T node for DC
        sim.deploy_module(app, "DC", services["DC"], rand.choice(T_nodes_ids))

        # Jedan NR cvor u regiji.
        # Dekompresija na GW.




