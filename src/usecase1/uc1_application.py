from application import Application, Message
from population import Population, Statical
from distribution import uniformDistribution
from uc1_distribution import DeterministicDistribution_mm_uc1.

class Uc1_application(object):

    def __init__(self, N=1, h=1, d=1, P=1, M=1, compression=None, compressionRatio=0.6):
        self.app = Application(name="UseCase1")

        # TODO: sanity check of parameters.
        # multipliers for datasets. see .doc where use-case1 is explained.
        self.N = N  # number of instruction multiplier
        self.h = h  # instruction header multiplier
        self.d = d  # instruction data multiplier
        self.P = P  # multiplier for processing power in all nodes and memory in NR and GW
        self.M = M  # multiplier for memory in MM and GW

        self.compression = compression
        self.compressionRatio = compressionRatio

        self.msgs = tuple()

        # TODO: Check parameters, the P and M in docs, are those scalings?
        self.app.set_modules([
            {"MM": {"RAM": self.M, "IPT": self.P, "Type":Application.TYPE_SOURCE}},
            {"GW": {"RAM": 100*self.M, "IPT": 20*self.P, "Type":Application.TYPE_MODULE}},
            {"NR": {"RAM": 60*self.P, "IPT": 500*self.P, "Type":Application.TYPE_MODULE}},
            {"DC": {"RAM": 1000*self.P, "IPT": 10000*self.P, "Type":Application.TYPE_SINK}},
        ])

        # COMP -> Compression, PROC -> DataProcessing
        MM_GW_m = Message("MM_GW_m", "MM", "GW", instructions=self.__calcOktets(1),
                          bytes=self.__calcInstruction(20, 16))
        PROC_DC_m = Message("PROC_DC_m", "PROC", "DC", instructions=self.__calcOktets(8),
                            bytes=self.__calcInstruction(60, 27))
        # TODO: maybe uncessary
        #NR_NR_m = Message("NR_NR_m", "NR", "NR", instructions=self.__calcOktets(8),
        #                   bytes=self.__calcInstruction(60, 27))

        GW_COMP_m = Message("GW_COMP_m", "GW", "COMP", instructions=self.__calcOktets(6),
                            bytes=self.__calcInstruction(40, 16))
        COMP_NR_m = Message("COMP_NR_m", "COMP", "NR",  instructions=self.__calcOktets(3),
                            bytes=self.__calcInstruction(60, 27))
        NR_PROC_m = Message("NR_PROC_m", "NR", "PROC", instructions=self.__calcOktets(12),
                            bytes=self.__calcInstruction(60, 27))

        GW_NR_m = Message("GW_NR_m", "GW", "NR", instructions=self.__calcOktets(3),
                          bytes=self.__calcInstruction(40, 16))
        NR_COMP_m = Message("NR_COMP_m", "NR", "COMP", instructions=self.__calcOktets(6),
                            bytes=self.__calcInstruction(60, 16))
        COMP_PROC_m = Message("COMP_PROC_m", "COMP", "PROC", instructions=self.__calcOktets(12),
                              bytes=self.__calcInstruction(60, 27))

        # TODO:  MARKO check how to implement cases. Za početak makni komplex try only necessary.
        # source is added above in modules.
        self.app.add_service_module("GW", MM_GW_m, GW_NR_m)  # TODO: MARKO na gw modulu se ustvari može odrediti daljni flow poruka. Tj hocemo li kompresiu prije ili posije NR-a. U ovisnosti koju od ove dvije poruke ce posalti.
        self.app.add_service_module("GW", MM_GW_m, GW_COMP_m)
        self.app.add_service_module("NR", GW_NR_m, NR_COMP_m)
        self.app.add_service_module("NR", COMP_NR_m, NR_PROC_m)
        #self.app.add_service_module("NR", NR_NR_m, NR_NR_m) # TODO: maybe unnecessary
        self.app.add_service_module("COMP", GW_COMP_m, COMP_NR_m)
        self.app.add_service_module("COMP", NR_COMP_m, COMP_PROC_m)
        self.app.add_service_module("PROC", COMP_PROC_m, PROC_DC_m)
        self.app.add_service_module("PROC", NR_PROC_m, PROC_DC_m)

        distribution = DeterministicDistribution_mm_uc1(15)
        self.app.add_service_source("MM", message=MM_GW_m, distribution=distribution)

    def __calcOktets(self, ratio):
        return ratio * self.N

    def __calcInstruction(self, header, data):
        return header*self.h + data*self.d
