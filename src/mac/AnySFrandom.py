from src.base import *
from src.mac.Scheduler import Scheduler

class AnySFrandom(Scheduler):

    def __init__(self, numDevices, slottime, timeslots, numLRchannels, availableSF_data) -> None:
        super().__init__(numDevices, slottime, timeslots, numLRchannels, availableSF_data)


    def get_schedule(self, timeshift=0):

        lora_schedules = []
        lrfhss_scheduels = []
        for n in range(self.N):

            random_timeslot = np.random.randint(0, self.W - self.T_m[-1]) + timeshift
            random_channel = np.random.choice(list(range(self.LRchannels)))

            # use LoRa SF11 or SF12 with 50/50 probability
            if random.random() < 0.5:
                m = np.random.choice([4,5])
                lora_schedules.append((n, m, random_timeslot, random_channel))

            # or use LRFHSS CR1/3 or CR2/3 with 50/50 probability
            else:
                m = np.random.choice([6,7])
                lrfhss_scheduels.append((n, m, random_timeslot, 1))
        
        return lora_schedules, lrfhss_scheduels
