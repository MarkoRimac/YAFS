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
            result = self.time
        return result

# Definira postotak M cvorova koji se nalaze u vise regija
# 65% da ce biti u jednoj regiji
# 20% u dvije regije
# 10% u tri regije
# 5% u cetiri regije
class Distribution_of_core_nodes_in_regions(Distribution):
    def __init__(self, **kwargs):
        super(Distribution_of_core_nodes_in_regions, self).__init__(**kwargs)

    def next(self):
        x = random.random()
        if x < 0.65:
            return 1
        elif 0.65 <= x < 0.85:
            return 2
        elif 0.85 <= x < 0.95:
            return 3
        elif 0.95 <= x <= 1:
            return 4
