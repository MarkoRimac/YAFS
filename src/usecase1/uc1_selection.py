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
        bestPaths = []
        bestDESs = []
        #print (DES_dst)

        if message.name == self.messageToBeFiltered:
            if message.id in self.forwardedMessages:
                message.dst = "NR_SINK" #  FORWARDAJ PORUKU NA SINK!
                DES_dst = alloc_module[app_name]["NR_SINK"]
                bestPaths = [[node_src]]
                for des in DES_dst: #  Nadi NR_SINK DES proces na src cvoru
                    if alloc_DES[des] == node_src:
                        bestDESs = [des]
                        break
                return bestPaths, bestDESs
            self.forwardedMessages.append(message.id)


        if message.dst == message.src: # Idi u sebe! Za poruke tipa NR->NR
            bestPaths = [[node_src]]
            bestDESs = [from_des]
        elif message.dst == "GW":
            for des in DES_dst:
                dst_node = alloc_DES[des]
                # print "DES Node %i " %dst_node
                paths = list(nx.all_simple_paths(sim.topology.G, source=node_src, target=dst_node,cutoff=1))  # Distance izmedu MM i GW je samo 1!
                for path in paths:
                    bestPaths.append(path) #  Vise pathova ce se poslati MM-u. To ce uzrokovat da dode do broadcastinga MM poruka na vise GW cvorova!
                    bestDESs.append(des)
        elif message.dst == "NR_FILT":
            best_des = dict()  # Saves DES for corresponding path.
            for des in DES_dst:
                dst_node = alloc_DES[des]
                # print "DES Node %i " %dst_node
                path = list(nx.shortest_path(sim.topology.G, source=node_src, target=dst_node))
                if sim.topology.G.nodes[topology_src]['regions'] != sim.topology.G.nodes[path[-1]]['regions']:  # Ako taj DES_dst od NR-a nije namjenjen za tu regiju, NE DAJ PUTEVE za to! Pretpostavljda da imamo zasebne NR-ove za svaku regiju!
                    continue
                bestPaths.append(path)
                bestDESs.append(des)
                best_des[str(path)] = des

            # Dohvati najkraci.
            min(bestPaths, key=len)
            path = random.choice(bestPaths)  # Nekada su duljine puteva do NR cvorova iste za vise NR cvorova. Odaberi randomly koji ces. Ovdje je mogce upotrijebiti neku jos dodatnu metriku za odabir sljedeceg NR cvora ako ih je vise unutar jedne regije!
            bestPaths = [path]
            bestDESs = [best_des[str(path)]]
        else:
            best_des = dict()  # Saves DES for corresponding path.
            for des in DES_dst:
                dst_node = alloc_DES[des]
                # print "DES Node %i " %dst_node

                path = list(nx.shortest_path(sim.topology.G, source=node_src, target=dst_node))
                bestPaths.append(path)
                bestDESs.append(des)
                best_des[str(path)] = des

            # Dohvati najkraci.
            min(bestPaths, key=len)
            path = random.choice(bestPaths) # Nekada su duljine puteva do NR cvorova iste za vise NR cvorova. Odaberi randomly koji ces. Ovdje je mogce upotrijebiti neku jos dodatnu metriku za odabir sljedeceg NR cvora ako ih je vise unutar jedne regije!
            bestPaths = [path]
            bestDESs = [best_des[str(path)]]

        return bestPaths,bestDESs