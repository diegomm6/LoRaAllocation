from src.base import *
from src.mac.Scheduler import Scheduler

class LorawanClassA(Scheduler):

    def __init__(self, numDevices, slottime, timeslots, numLRchannels, availableSF_data) -> None:
        super().__init__(numDevices, slottime, timeslots, numLRchannels, availableSF_data)
    

    # Generate uplink schedules for Class A
    # assign a random start time and random SF
    def get_schedule(self):

        self.bestSF_n = self.get_best_SF_per_ed()

        lora_schedules = []
        for n in range(self.N):

            m_n = self.bestSF_n[n]
            # skip nodes without link support
            if m_n == -1: continue
            
            m_n -= self.bestSF
            i = n + m_n*self.N

            #random_sf = np.random.choice(self.availableSF_per_node[n])
            possible_schedules = np.where(self.delta[i][:])[0]
            random_timeslot = np.random.choice(possible_schedules)
            random_channel = np.random.choice(list(range(self.LRchannels)))

            lora_schedules.append((i, random_timeslot, random_channel))
        
        return lora_schedules

