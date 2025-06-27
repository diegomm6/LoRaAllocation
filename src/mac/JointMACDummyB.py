from src.base import *
from src.mac.Scheduler import Scheduler

class JointMACDummyB(Scheduler):

    def __init__(self, numDevices, slottime, timeslots, numLRchannels, availableSF_data) -> None:
        super().__init__(numDevices, slottime, timeslots, numLRchannels, availableSF_data)

        self.competitors_m = self.get_competitors()

    # calculate number of nodes achieving each SF as its best SF
    def get_competitors(self):

        competitors_m = np.zeros((self.M - self.bestSF))
        for m in range(self.M - self.bestSF):
            competitors_m[m] = np.sum(self.bestSF_n[:] == m+self.bestSF)

        return competitors_m


    def get_schedule(self):

        lora_schedules = []
        lrfhss_scheduels = []
        for n in range(self.N):

            m_n = self.bestSF_n[n] # m_n: best SF for ED n

            # skip nodes without link support
            if m_n == -1: continue

            lora_support = True
            if m_n > 5: lora_support = False

            competitors = self.competitors_m[m_n - self.bestSF]
            tx_prob = LoRA_success_prob(m_n+7, competitors)

            # use LoRa with best SF
            if lora_support and (random.random() < tx_prob):

                i = n + (m_n - self.bestSF) * self.N
                possible_schedules = np.where(self.delta[i][:])[0]
                random_timeslot = np.random.choice(possible_schedules)
                random_channel = np.random.choice(list(range(self.LRchannels)))

                lora_schedules.append((n, m_n, random_timeslot, random_channel))

            # or use LRFHSS CR1/3 or CR2/3 with 50/50 probability
            else:
                m = np.random.choice([6,7])
                random_timeslot = np.random.randint(0, self.W - self.T_m[-1])
                lrfhss_scheduels.append((n, m, random_timeslot, 1))
        
        return lora_schedules, lrfhss_scheduels
