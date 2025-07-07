from src.base import *
from src.mac.Scheduler import Scheduler

class ValidSFrandom(Scheduler):

    def __init__(self, numDevices, slottime, timeslots, numLRchannels, availableSF_data) -> None:
        super().__init__(numDevices, slottime, timeslots, numLRchannels, availableSF_data)

        self.SFavailability = self.get_SFavailability()


    # get a list of available SF for each node
    def get_SFavailability(self):

        SFavailability = np.zeros((self.N, self.M - self.bestSF), dtype=bool)

        for n in range(self.N):
            for m in range(self.M - self.bestSF):
                i = n + m*self.N
                if np.any(self.delta[i][:]):
                    SFavailability[n][m] = True

        return SFavailability


    def get_schedule(self, timeshift=0):

        lora_schedules = []
        lrfhss_scheduels = []
        for n in range(self.N):

            possible_m = np.where(self.SFavailability[n])[0]

            # use LoRa SF11 or SF12 with 50/50 probability
            if random.random() < 0.5 and  possible_m.size > 0:

                m = np.random.choice(possible_m) + self.bestSF
                i = n + (m - self.bestSF) * self.N
                
                possible_schedules = np.where(self.delta[i][:])[0]
                random_timeslot = np.random.choice(possible_schedules) + timeshift
                random_channel = np.random.choice(list(range(self.LRchannels)))

                lora_schedules.append((n, m, random_timeslot, random_channel))

            # or use LRFHSS CR1/3 or CR2/3 with 50/50 probability
            else:
                m = np.random.choice([6,7])
                random_timeslot = np.random.randint(0, self.W - self.T_m[-1]) + timeshift
                lrfhss_scheduels.append((n, m, random_timeslot, 1))
        
        return lora_schedules, lrfhss_scheduels
