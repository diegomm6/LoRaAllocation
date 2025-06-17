from src.base import *
from src.mac.Scheduler import Scheduler

class JointDummyMAC(Scheduler):

    def __init__(self, numDevices, slottime, timeslots, numLRchannels, availableSF_data) -> None:
        super().__init__(numDevices, slottime, timeslots, numLRchannels, availableSF_data)


    def get_schedule(self):

        self.bestSF_n = self.get_best_SF_per_ed()

        schedules = []
        for n in range(self.N):

            # use SF11 or SF12 with 50/50 probability
            if random.random() < 0.5:
                m = np.random.choice([11,12])

            # or use CR1/3 or CR2/3 with 50/50 probability
            else:
                m = np.random.choice([13,14])


            random_timeslot = np.random.randint(0, self.W)
            random_channel = np.random.choice(list(range(self.LRchannels)))

            schedules.append((m, random_timeslot, random_channel))
        
        return schedules
