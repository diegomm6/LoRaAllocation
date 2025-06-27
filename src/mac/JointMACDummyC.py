from src.base import *
from src.mac.Scheduler import Scheduler

class JointMACDummyC(Scheduler):

    def __init__(self, numDevices, slottime, timeslots, numLRchannels, availableSF_data) -> None:
        super().__init__(numDevices, slottime, timeslots, numLRchannels, availableSF_data)

        self.competitors_m = self.get_competitors()
        self.real_competitors_m = self.get_real_competitors()

    # calculate number of nodes achieving each SF as its best SF
    def get_competitors(self):

        competitors_m = np.zeros((self.M - self.bestSF))
        for m in range(self.M - self.bestSF):
            competitors_m[m] = np.sum(self.bestSF_n[:] == m+self.bestSF)

        return competitors_m
    
    # calculate total number of competitors considering multiple SF choices
    def get_real_competitors(self):

        self.TX_prob_m = np.zeros((self.M - self.bestSF))
        real_competitors_m = np.zeros((self.M - self.bestSF))
        
        self.TX_prob_m[0] = LoRA_success_prob(self.bestSF + 7, self.competitors_m[0])
        real_competitors_m[0] = self.competitors_m[0]

        for m in range(1, self.M - self.bestSF):
            real_competitors_m[m] = self.competitors_m[m] + (1 - self.TX_prob_m[m-1]) * real_competitors_m[m-1]
            self.TX_prob_m[m] = LoRA_success_prob(m + self.bestSF + 7, real_competitors_m[m])
        
        return real_competitors_m


    def get_schedule(self):

        lora_schedules = []
        lrfhss_scheduels = []
        for n in range(self.N):

            m_n = self.bestSF_n[n] # m_n: best SF for ED n
            if m_n == -1: continue # skip nodes without link support

            # try using SFs while there is lora support, then use lrfhss
            used_lora = False
            while (m_n <= 5 and not used_lora):

                if random.random() < self.TX_prob_m[m_n - self.bestSF]:

                    i = n + (m_n - self.bestSF) * self.N
                    possible_schedules = np.where(self.delta[i][:])[0]

                    # if this SF is not available anytime, move to the next one
                    if not possible_schedules.any():
                        m_n += 1
                        continue 

                    random_timeslot = np.random.choice(possible_schedules)
                    random_channel = np.random.choice(list(range(self.LRchannels)))

                    lora_schedules.append((n, m_n, random_timeslot, random_channel))
                    used_lora = True
                
                m_n += 1

            # or use LRFHSS CR1/3 or CR2/3 with 50/50 probability
            if not used_lora:
                m = np.random.choice([6,7])
                random_timeslot = np.random.randint(0, self.W - self.T_m[-1])
                lrfhss_scheduels.append((n, m, random_timeslot, 1))
        
        return lora_schedules, lrfhss_scheduels
