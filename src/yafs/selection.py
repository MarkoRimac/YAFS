"""
    This algorithm have one obligatory functions:

        *get_path*: It provides the route to follow the message within the topology to reach the destination module, it can also be seen as an orchestration algorithm.


"""
import random
import logging

import networkx as nx


class Selection(object):
    """
    A selection algorithm provide the route among topology entities for that a message reach the destiny module.

    .. note:: A class interface
    """

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.transmit = 0.0
        self.lat_acc = 0.0
        self.propagation = 0.0

    def get_path(self, sim, app_name, message, topology_src,alloc_DES, alloc_module, traffic, from_des):

        """
        Args:

        :param sim:
        :param message:
        :param link:
        :param alloc_DES:
        :param alloc_module:
        :param traffic:
        :param ctime:
        :param from_des
        :return:
           both empty arrays implies that the message will not send to the destination.

        Returns:

            a path among nodes

            an identifier of the module

        .. attention:: override required

        """
        self.logger.debug("Selection")
        """ Define Selection """
        path = []
        ids = []

        """ END Selection """
        return path,ids

    def get_path_from_failure(self, sim, message, link, alloc_DES, alloc_module, traffic, ctime, from_des):
        """
        This function is call when some link of a message path is broken or unavailable. A new one from that point should be calculated.

        :param sim:
        :param message:
        :param link:
        :param alloc_DES:
        :param alloc_module:
        :param traffic:
        :param ctime:
        :param from_des
        :return:
           both empty arrays implies that the message will not send to the destination.

        .. attention:: this function is optional
        """
        """ Define Selection """
        path = []
        ids = []

        """ END Selection """
        return path, ids

class OneRandomPath(Selection):
    """
    Among all the possible options, it returns a random path.
    """

    def get_path(self, sim, app_name, message, topology_src,alloc_DES, alloc_module, traffic,from_des):
        paths = []
        dst_idDES = []
        src_node = topology_src
        DES = alloc_module[message.app_name][message.dst]
        for idDES in DES:
            dst_node = alloc_module[idDES]
            pathX = list(nx.all_simple_paths(sim.topology.G, source=src_node, target=dst_node))
            one = random.randint(0, len(pathX) - 1)
            paths.append(pathX[one])
            dst_idDES.append(idDES)
        return paths,dst_idDES



class First_ShortestPath(Selection):
    """Among all possible shorter paths, returns the first."""

    def __init__(self, messageToBeFiltered):
        self.messageToBeFiltered = messageToBeFiltered
        self.forwardedMessages = list()
        super(First_ShortestPath, self).__init__()


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
            for des in DES_dst:
                dst_node = alloc_DES[des]
                # print "DES Node %i " %dst_node

                path = list(nx.shortest_path(sim.topology.G, source=node_src, target=dst_node))
                bestPath = [path]
                bestDES  = [des]
                #print (path)

        return bestPath,bestDES
