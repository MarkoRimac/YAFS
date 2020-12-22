from application import Application, Message
from population import Population, Statical
from distribution import uniformDistribution
from uc1_distribution import DeterministicDistribution_mm_uc1


class Uc1_application(object):

    def __init__(self, app_name, app_version, topology, N=1, h=1, d=1, P=1, M=1, decompressionRatio=0.6):
        self.app = Application(name=app_name)

        self.topology = topology
        # TODO: sanity check of parameters.
        # multipliers for datasets. see .doc where use-case1 is explained.
        self.N = N  # number of instruction multiplier
        self.h = h  # instruction header multiplier
        self.d = d  # instruction data multiplier
        self.P = P  # multiplier for processing power in all nodes and memory in NR and GW
        self.M = M  # multiplier for memory in MM and GW
        self.compressionRatio = decompressionRatio

        # KONSTANTE
        self.SOURCE_GENERATION_PERIOD_s = 15 # Period od 15s za generiranje poruka u MM
        self.decompressed_data = 27
        self.compressed_data = self.decompressed_data * self.compressionRatio


        #HELPERS
        self.msgs = tuple()

        if app_version == "DECOMP_FILT":
            self.__do_DECOMP_FILT()
        elif app_version == "FILT_DECOMP":
            self.__do_FILT_DECOMP()
        else:
            self.__do_NONE()

    def __calcOktets(self, ratio):
        return ratio * self.N

    def __calcInstruction(self, header, data):
        return header*self.h + data*self.d

    def __do_FILT_DECOMP(self):
        # TODO: Modify parameters.
        self.app.set_modules([  # SVAKI MODUL IMA PROCES, "DES" za sebe, i queue na sebi!
            {"MM": {"RAM": self.M, "IPT": self.P, "Type": Application.TYPE_SOURCE}},
            # Za sto sluzi RAM? Nigdje u coru se ne pojavljuje da se ista racuna s njim, a u IEEE tekstu pise da je "obavezan".
            {"GW": {"RAM": 100 * self.M, "IPT": 20 * self.P, "Type": Application.TYPE_MODULE}},
            {"NR_FILT": {"RAM": 60 * self.P, "IPT": 500 * self.P, "Type": Application.TYPE_MODULE}},
            # TODO Filtracija i Dekompresija ce biti zasebni procesi na istom cvoru. Kako napraviti shareanje resursa IPT-a? Za sada sam stavio da svaki ima svoj IPT koji koristi, ISTO I DOLJE RADIM SA dva procesa na DC!
            {"NR_DECOMP": {"RAM": 60 * self.P, "IPT": 500 * self.P, "Type": Application.TYPE_MODULE}},
            {"NR_SINK": {"Type": Application.TYPE_SINK}},
            # PURE SINK! Modul za sebe, koji će se staviti na isti čvor na kojem su NR-ovi. On  će služiti kao sink za poruke koje su se zaprimile više puta, RAM i IPT za takav modul nisu bitni!
            {"DC_PROC": {"RAM": 1000 * self.P, "IPT": 10000 * self.P, "Type": Application.TYPE_MODULE}},
            {"DC_STORAGE": {"RAM": 1000 * self.P, "IPT": 10000 * self.P, "Type": Application.TYPE_MODULE}},
            # Servis za timeout na "storage" i servis za "sink". U outputu csv-a ne dobijemo ovu poruku.
        ])

        # DECOMP -> decompression, PROC -> DataProcessing
        MM_GW_m = Message("MM_GW_m", "MM", "GW", instructions=self.__calcOktets(1),
                          bytes=self.__calcInstruction(20, self.compressed_data)) # Kompresija na MMu
        GW_NR_FILT_m = Message("GW_NR_FILT_m", "GW", "NR_FILT", instructions=self.__calcOktets(3),
                               bytes=self.__calcInstruction(40, self.compressed_data))  # Filtracija
        NR_FILT_NR_DECOMP_m = Message("NR_FILT_NR_DECOMP_m", "NR_FILT", "NR_DECOMP", instructions=self.__calcOktets(6),
                                      bytes=self.__calcInstruction(60, self.compressed_data))  # DEKOMPRESIJA; poruka koja se "filtrira" - izbacuje - ne salje dalje, ako je duplikat. u selectionu joj se mijenja "msg.dest" na sink ako je za filtraciju
        NR_DECOMP_DC_PROC_m = Message("NR_DECOMP_DC_PROC_m", "NR_DECOMP", "DC_PROC", instructions=self.__calcOktets(12),
                                      bytes=self.__calcInstruction(60, self.decompressed_data))  # PROCESSING time
        DC_PROC_DC_STORAGE_m = Message("DC_PROC_DC_STORAGE_m", "DC_PROC", "DC_STORAGE", instructions=self.__calcOktets(8),
                                       bytes=self.__calcInstruction(60, self.decompressed_data))  # STORAGE time

        # Filtracija pa Dekompozicija
        # source is added above in modules.
        self.app.add_service_module("GW", MM_GW_m, GW_NR_FILT_m)
        self.app.add_service_module("NR_FILT", GW_NR_FILT_m, NR_FILT_NR_DECOMP_m)
        self.app.add_service_module("NR_DECOMP", NR_FILT_NR_DECOMP_m, NR_DECOMP_DC_PROC_m)
        self.app.add_service_module("DC_PROC", NR_DECOMP_DC_PROC_m, DC_PROC_DC_STORAGE_m)

        """ POPULATION """
        self.app.add_service_module("DC_STORAGE", DC_PROC_DC_STORAGE_m)  # Ide na timeout za storing koji je def u DC_PROC_DC_STORAGE_m poruci, i dalje je SINK pa zato nema "dest" poruku!
        #  self.app.add_service_module("NR_SINK", NR_DECOMP_m)  # NE RADIM OVO, jer sam ga gore definirao kao PURE SINK MODUL! Ostavio sam ovu liniju cisto da se lakse vidi sta ne treba radit

        distribution = DeterministicDistribution_mm_uc1(15, self.topology.my_as_graph.total_num_of_mm,
                                                        name="deterministicMM")
        self.app.add_service_source("MM", message=MM_GW_m, distribution=distribution)
        self.app.add_source_messages(MM_GW_m)

        """ END OF POPULATION"""

    def __do_DECOMP_FILT(self):

        # TODO: Modify parameters.
        self.app.set_modules([  # SVAKI MODUL IMA PROCES, "DES" za sebe, i queue na sebi!
            {"MM": {"RAM": self.M, "IPT": self.P, "Type": Application.TYPE_SOURCE}},
            # Za sto sluzi RAM? Nigdje u coru se ne pojavljuje da se ista racuna s njim, a u IEEE tekstu pise da je "obavezan".
            {"GW": {"RAM": 100 * self.M, "IPT": 20 * self.P, "Type": Application.TYPE_MODULE}},
            {"NR_FILT": {"RAM": 60 * self.P, "IPT": 500 * self.P, "Type": Application.TYPE_MODULE}}, # TODO Filtracija i Dekompresija ce biti zasebni procesi na istom cvoru. Kako napraviti shareanje resursa IPT-a? Za sada sam stavio da svaki ima svoj IPT koji koristi, ISTO I DOLJE RADIM SA dva procesa na DC!
            {"NR_DECOMP": {"RAM": 60 * self.P, "IPT": 500 * self.P, "Type": Application.TYPE_MODULE}},
            {"NR_SINK": {"Type": Application.TYPE_SINK}}, # PURE SINK! Modul za sebe, koji će se staviti na isti čvor na kojem su NR-ovi. On  će služiti kao sink za poruke koje su se zaprimile više puta, RAM i IPT za takav modul nisu bitni!
            {"DC_PROC": {"RAM": 1000 * self.P, "IPT": 10000 * self.P, "Type": Application.TYPE_MODULE}},
            {"DC_STORAGE": {"RAM": 1000 * self.P, "IPT": 10000 * self.P, "Type": Application.TYPE_MODULE}}, # Servis za timeout na "storage" i servis za "sink". U outputu csv-a ne dobijemo ovu poruku.
        ])

        # DECOMP -> decompression, PROC -> DataProcessing
        MM_GW_m =              Message("MM_GW_m", "MM", "GW",
                                        instructions=self.__calcOktets(1),
                                        bytes=self.__calcInstruction(20, self.compressed_data))  # komprsirani podatci
        GW_NR_DECOMP_m =       Message("GW_NR_DECOMP_m", "GW", "NR_DECOMP",
                                        instructions=self.__calcOktets(6),
                                        bytes=self.__calcInstruction(40, self.compressed_data))  # dekompresija nema utjecaja FILTRACIJU
        NR_DECOMP_NR_FILT_m =  Message("NR_DECOMP_NR_FILT_m", "NR_DECOMP", "NR_FILT",
                                        instructions=self.__calcOktets(3),
                                        bytes=self.__calcInstruction(60, self.decompressed_data))  # dekompresija nema utjecaja na network, tu sam stavio jer je i u
        NR_FILT_DC_PROC_m =    Message("NR_FILT_DC_PROC_m", "NR_FILT", "DC_PROC",
                                        instructions =self.__calcOktets(12),
                                        bytes =self.__calcInstruction(60, self.decompressed_data))  # PROCESSING time
        DC_PROC_DC_STORAGE_m = Message("DC_PROC_DC_STORAGE_m", "DC_PROC", "DC_STORAGE",
                                        instructions=self.__calcOktets(8),
                                        bytes=self.__calcInstruction(60, self.decompressed_data))  # STORAGE time

        # Filtracija pa Dekompozicija
        # source is added above in modules.
        self.app.add_service_module("GW", MM_GW_m, GW_NR_DECOMP_m)
        self.app.add_service_module("NR_DECOMP", GW_NR_DECOMP_m, NR_DECOMP_NR_FILT_m)
        self.app.add_service_module("NR_FILT", NR_DECOMP_NR_FILT_m, NR_FILT_DC_PROC_m)
        self.app.add_service_module("DC_PROC", NR_FILT_DC_PROC_m, DC_PROC_DC_STORAGE_m)

        """ POPULATION """
        self.app.add_service_module("DC_STORAGE",
                                    DC_PROC_DC_STORAGE_m)  # Ide na timeout za storing koji je def u DC_PROC_DC_STORAGE_m poruci, i dalje je SINK pa zato nema "dest" poruku!
        #  self.app.add_service_module("NR_SINK", NR_DECOMP_m)  # NE RADIM OVO, jer sam ga gore definirao kao PURE SINK MODUL! Ostavio sam ovu liniju cisto da se lakse vidi sta ne treba radit

        distribution = DeterministicDistribution_mm_uc1(self.SOURCE_GENERATION_PERIOD_s, self.topology.my_as_graph.total_num_of_mm,
                                                        name="deterministicMM")
        self.app.add_service_source("MM", message=MM_GW_m, distribution=distribution)
        self.app.add_source_messages(MM_GW_m)

        """ END OF POPULATION"""

    def __do_NONE(self):
        # TODO: Modify parameters.
        self.app.set_modules([  # SVAKI MODUL IMA PROCES, "DES" za sebe, i queue na sebi!
            {"MM": {"RAM": self.M, "IPT": self.P, "Type": Application.TYPE_SOURCE}},
            # Za sto sluzi RAM? Nigdje u coru se ne pojavljuje da se ista racuna s njim, a u IEEE tekstu pise da je "obavezan".
            {"GW": {"RAM": 100 * self.M, "IPT": 20 * self.P, "Type": Application.TYPE_MODULE}},
            {"NR_FILT": {"RAM": 60 * self.P, "IPT": 500 * self.P, "Type": Application.TYPE_MODULE}},
            # TODO Filtracija i Dekompresija ce biti zasebni procesi na istom cvoru. Kako napraviti shareanje resursa IPT-a? Za sada sam stavio da svaki ima svoj IPT koji koristi, ISTO I DOLJE RADIM SA dva procesa na DC!
            {"NR_DECOMP": {"RAM": 60 * self.P, "IPT": 500 * self.P, "Type": Application.TYPE_MODULE}}, # Not really used here.
            {"NR_SINK": {"Type": Application.TYPE_SINK}},
            # PURE SINK! Modul za sebe, koji će se staviti na isti čvor na kojem su NR-ovi. On  će služiti kao sink za poruke koje su se zaprimile više puta, RAM i IPT za takav modul nisu bitni!
            {"DC_PROC": {"RAM": 1000 * self.P, "IPT": 10000 * self.P, "Type": Application.TYPE_MODULE}},
            {"DC_STORAGE": {"RAM": 1000 * self.P, "IPT": 10000 * self.P, "Type": Application.TYPE_MODULE}},
            # Servis za timeout na "storage" i servis za "sink". U outputu csv-a ne dobijemo ovu poruku.
        ])

        # DECOMP -> decompression, PROC -> DataProcessing
        MM_GW_m = Message("MM_GW_m", "MM", "GW", instructions=self.__calcOktets(1),
                          bytes=self.__calcInstruction(20, self.decompressed_data)) # Kompresija na MMu
        GW_NR_FILT_m = Message("GW_NR_FILT_m", "GW", "NR_FILT", instructions=self.__calcOktets(3),
                               bytes=self.__calcInstruction(40, self.decompressed_data))  # Filtracija
        NR_FILT_DC_PROC_m = Message("NR_FILT_DC_PROC_m", "NR_FILT", "DC_PROC", instructions=self.__calcOktets(12),
                                      bytes=self.__calcInstruction(60, self.decompressed_data))  # PROCESSING time
        DC_PROC_DC_STORAGE_m = Message("DC_PROC_DC_STORAGE_m", "DC_PROC", "DC_STORAGE", instructions=self.__calcOktets(8), # STORAGE time
                                       bytes=self.__calcInstruction(60, self.decompressed_data))
        DUMMY_MESSAGE_m = Message("DUMMY_MESSAGE_m", "sada", "sads") # ovo je ovde samo da se sprijece if-ovi za app_version u uc1_placementu. NR_DECOMP kao "postoji" ali ustvari ga skros zaobilazimo.

        # Filtracija pa Dekompozicija
        # source is added above in modules.
        self.app.add_service_module("GW", MM_GW_m, GW_NR_FILT_m)
        self.app.add_service_module("NR_FILT", GW_NR_FILT_m, NR_FILT_DC_PROC_m)
        self.app.add_service_module("DC_PROC", NR_FILT_DC_PROC_m, DC_PROC_DC_STORAGE_m)
        self.app.add_service_module("NR_DECOMP", DUMMY_MESSAGE_m, DUMMY_MESSAGE_m) # ovo je ovde samo da se sprijece if-ovi za app_version u uc1_placementu. NR_DECOMP kao "postoji" ali ustvari ga skros zaobilazimo.


        """ POPULATION """
        self.app.add_service_module("DC_STORAGE",
                                    DC_PROC_DC_STORAGE_m)  # Ide na timeout za storing koji je def u DC_PROC_DC_STORAGE_m poruci, i dalje je SINK pa zato nema "dest" poruku!
        #  self.app.add_service_module("NR_SINK", NR_DECOMP_m)  # NE RADIM OVO, jer sam ga gore definirao kao PURE SINK MODUL! Ostavio sam ovu liniju cisto da se lakse vidi sta ne treba radit

        distribution = DeterministicDistribution_mm_uc1(15, self.topology.my_as_graph.total_num_of_mm,
                                                        name="deterministicMM")
        self.app.add_service_source("MM", message=MM_GW_m, distribution=distribution)
        self.app.add_source_messages(MM_GW_m)

        """ END OF POPULATION"""