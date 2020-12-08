from yafs.distribution import Distribution
import random

class DeterministicDistribution_mm_uc1(Distribution):
    def __init__(self,time, **kwargs):
        self.start = 0
        self.time = time
        self.started = False
        super(DeterministicDistribution_mm_uc1, self).__init__(**kwargs)

    def next(self):
        if not self.started:
            self.started = True
            self.start = random.randint(0, self.time) # make it start randomly between 0-15 then repeat every 15 min.
            return self.start
        else:
            return self.time