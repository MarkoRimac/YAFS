from yafs.application import Application, Message

class Uc1_application(object):

    def __init__(self, n, h, d, compression=None, compressionRatio=0.6):
        self.app = Application(name="UseCase1")
        # TODO: > 0
        self.n = 1
        self.h = 1
        self.d = 1
        self.n = n
        self.h = h
        self.d = d

        self.compression = compression
        self.compressionRatio =  compressionRatio

    def __set_modules(self):
        # TODO: Check parameters, the P in .doc?
        # DCO -> Decompossition, DPR -> DataProcessing
        self.app.set_modules({
            {"MM":{"RAM": 1, "IPT": 1, "Type":Application.TYPE_MODULE}},
            {"GW":{"RAM": 100, "IPT": 20, "Type":Application.TYPE_MODULE}},
            {"NR":{"RAM": 600, "IPT": 500, "Type":Application.TYPE_MODULE}},
            {"DC":{"RAM": 10000, "IPT": 10000, "Type":Application.TYPE_MODULE}},
            {"COMP": {"Type": Application.TYPE_MODULE, "CompressionRatio": self.compressionRatio}},# Their RAM and IPT is based on what node they are allocated.)
            {"PROC":{"Type":Application.TYPE_MODULE}}
        })

        MM_GW_m = Message("MM_GW_m", "MM", "GW", instructions=self.__calcOktets(1),
                          bytes=self.__calcInstruction(20, 16))
        PROC_DC_m = Message("PROC_DC_m", "PROC", "DC", instructions=self.__calcOktets(8),
                            bytes=self.__calcInstruction(60, 27))

        if self.compression == "before":
            GW_COMP_m = Message("GW_COMP_m", "GW", "COMP", instructions=self.__calcOktets(6),
                                bytes=self.__calcInstruction(40, 16))
            COMP_NR_m = Message("COMP_NR_m", "COMP", "NR", instructions=self.__calcOktets(3),
                                bytes=self.__calcInstruction(60, 27))
            NR_PROC_m = Message("NR_PROC_m", "NR", "PROC", instructions=self.__calcOktets(12),
                                bytes=self.__calcInstruction(60, 27))

        elif self.compression == "after":
            GW_NR_m = Message("GW_NR_m", "GW", "NR", instructions=self.__calcOktets(3),
                              bytes=self.__calcInstruction(40, 16))
            NR_COMP_m = Message("NR_COMP_m", "NR", "COMP", instructions=self.__calcOktets(6),
                                bytes=self.__calcInstruction(60, 16))
            COMP_PROC_m = Message("COMP_PROC_m", "COMP", "PROC", instructions=self.__calcOktets(12),
                                  bytes=self.__calcInstruction(60, 27))
        else: # No decompression module.
            GW_NR_m = Message("GW_NR_m", "GW", "NR", instructions=self.__calcOktets(3),
                              bytes=self.__calcInstruction(40, 16))
            NR_PROC_m = Message("NR_PROC_m", "NR", "PROC", instructions=self.__calcOktets(12),
                                bytes=self.__calcInstruction(60, 27))


    def __calcOktets(self, ratio):
        return ratio * self.n

    def __calcInstruction(self, header, data):
        return header*self.h + header*self.d
