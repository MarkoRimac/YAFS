from yafs.distribution import Distribution
import random

class DeterministicDistribution_mm_uc1(Distribution):
    def __init__(self,time, nb_mm_nodes, **kwargs):
        self.start = 0
        self.time = time
        self.nb_mm_nodes = nb_mm_nodes
        self.index = 0
        self.startup_counter = nb_mm_nodes
        self.rand_start_values = dict()
        for x in range(self.nb_mm_nodes):
            self.rand_start_values[x] = random.randint(0, self.time)
        super(DeterministicDistribution_mm_uc1, self).__init__(**kwargs)

    def next(self):

        # na pocetku neka svi MM cvorovi krenu u [0,15], a onda kasnije, neka se novi zadatci stvaraju u periodi od self.time
        if self.startup_counter > 0:
            result = self.rand_start_values[self.index % self.nb_mm_nodes]
            self.index += 1
            self.startup_counter -= 1
        else:
            result = self.time + self.rand_start_values[self.index % self.nb_mm_nodes]
            self.index += 1
        return result