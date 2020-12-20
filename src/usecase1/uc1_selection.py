from yafs.selection import Selection
import networkx as nx
import random

class Uc1_First_ShortestPath(Selection):
    """Among all possible shorter paths, returns the first."""

    def __init__(self, messageToBeFiltered):
        self.messageToBeFiltered = messageToBeFiltered
        self.forwardedMessages = list()
        super(Uc1_First_ShortestPath, self).__init__()


    def get_path(self, sim, app_name,message, topology_src, alloc_DES, alloc_module, traffic,from_des):
        paths = []
        dst_idDES = []

        node_src = topology_src #TOPOLOGY SOURCE where the message is generated
        DES_dst = alloc_module[app_name][message.dst]

        #Among all possible path we choose the smallest
        bestPath = []
        bestDES = []
        #print (DES_dst)

        if message.name == self.messageToBeFiltered:
            if message.id in self.forwardedMessages:
                message.dst = "NR_SINK" #  FORWARDAJ PORUKU NA SINK!
                DES_dst = alloc_module[app_name]["NR_SINK"]
                bestPath = [[node_src]]
                for des in DES_dst: #  Nadi NR_SINK DES proces na src cvoru
                    if alloc_DES[des] == node_src:
                        bestDES = [des]
                        break
                return bestPath, bestDES
            self.forwardedMessages.append(message.id)


        if message.dst == message.src: # Idi u sebe! Za poruke tipa NR->NR
            bestPath = [[node_src]]
            bestDES = [from_des]
        elif message.dst == "GW":
            for des in DES_dst:
                dst_node = alloc_DES[des]
                # print "DES Node %i " %dst_node
                paths = list(nx.all_simple_paths(sim.topology.G, source=node_src, target=dst_node,cutoff=1))  # Distance izmedu MM i GW je samo 1!
                for path in paths:
                    bestPath.append(path) # TODO: Preimenuj ovaj bestPath.... Nije uvijek samo jedan! Ovdje je za broadcast od MM-a vise njih!!
                    bestDES.append(des)
        else:
            best_des = dict()  # Saves DES for corresponding path.
            for des in DES_dst:
                dst_node = alloc_DES[des]
                # print "DES Node %i " %dst_node

                path = list(nx.shortest_path(sim.topology.G, source=node_src, target=dst_node))
                bestPath.append(path)
                bestDES.append(des)
                best_des[str(path)] = des

            # Dohvati najkraci.
            min(bestPath, key=len)
            path = random.choice(bestPath) # Nekada su duljine puteva do NR cvorova iste za vise NR cvorova. Odaberi randomly koji ces. Ovdje je mogce upotrijebiti neku jos dodatnu metriku za odabir sljedeceg NR cvora ako ih je vise unutar jedne regije!
            bestPath = [path]
            bestDES = [best_des[str(path)]]

        return bestPath,bestDES