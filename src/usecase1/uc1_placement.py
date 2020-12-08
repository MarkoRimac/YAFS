from yafs.placement import Placement

class Uc1_placement(Placement):

    def initial_allocation(self, sim, app_name):
        #We find the ID-nodo/resource
        value = {"mytag": "cloud"} # or whatever tag

        id_cluster = sim.topology.find_IDs(value)
        app = sim.apps[app_name]
        services = app.services

        for module in services:
            if module in self.scaleServices:
                for rep in range(0, self.scaleServices[module]):
                    idDES = sim.deploy_module(app_name,module,services[module],id_cluster)

    #end function