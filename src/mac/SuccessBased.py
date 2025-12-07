from src.base import *
from src.mac.Scheduler import Scheduler

class SuccessBased(Scheduler):

    def __init__(self, numDevices, slottime, timeslots, numLRchannels, availableSF_data, th=.4, SFmode=0) -> None:
        super().__init__(numDevices, slottime, timeslots, numLRchannels, availableSF_data)

        self.threshold = th
        self.competitors_m = self.get_competitors()
        self.cumulative_competitors_m = self.get_cumulative_competitors()

        # two operation model
        # mode=0 allocates best SF
        # mode=1 uses sequential SF allocation
        self.SFmode = SFmode

    # calculate number of nodes achieving each SF as its best SF
    def get_competitors(self):

        competitors_m = np.zeros((self.M - self.bestSF))
        for m in range(self.M - self.bestSF):
            competitors_m[m] = np.sum(self.bestSF_n[:] == m+self.bestSF)

        return competitors_m


    # get cumulative competitors addign from previous sf
    def get_cumulative_competitors(self):
        cumulative_competitors_m = np.zeros((self.M - self.bestSF))
        cumulative_competitors_m[0] = self.competitors_m[0]

        for m in range(1, self.M - self.bestSF):
            cumulative_competitors_m[m] = cumulative_competitors_m[m-1] + self.competitors_m[m]

        return cumulative_competitors_m
    

    def get_schedule(self, timeshift=0):

        if self.SFmode == 0:
            return self.get_schedule_bestSF(timeshift)
        else:
            return self.get_schedule_seqSF(timeshift)
        

    def get_schedule_bestSF(self, timeshift=0):

        lora_schedules = []
        lrfhss_scheduels = []
        for n in range(self.N):

            m_n = self.bestSF_n[n] # m_n: best SF for ED n
            if m_n == -1: continue # skip nodes without link support

            maxEDs_th = max_num_ED(m_n+7, self.threshold) / self.competitors_m[m_n - self.bestSF]
            if (m_n <= 5) and (random.random() < maxEDs_th):

                i = n + (m_n - self.bestSF) * self.N
                possible_schedules = np.where(self.delta[i][:])[0]
                random_timeslot = np.random.choice(possible_schedules) + timeshift
                random_channel = np.random.choice(list(range(self.LRchannels)))

                lora_schedules.append((n, m_n, random_timeslot, random_channel))

            # or use LRFHSS CR1/3 or CR2/3 with 50/50 probability
            else:
                m = np.random.choice([6,7])
                random_timeslot = np.random.randint(0, self.W - self.T_m[-1]) + timeshift
                lrfhss_scheduels.append((n, m, random_timeslot, 1))
        
        return lora_schedules, lrfhss_scheduels
    

    def get_schedule_seqSF(self, timeshift=0):

        lora_schedules = []
        lrfhss_scheduels = []
        for n in range(self.N):

            m_n = self.bestSF_n[n] # m_n: best SF for ED n
            if m_n == -1: continue # skip nodes without link support

            # try using SFs while there is lora support, then use lrfhss
            used_lora = False
            while (m_n <= 5 and not used_lora):

                maxEDs_th = max_num_ED(m_n+7, self.threshold) / self.cumulative_competitors_m[m_n - self.bestSF]
                if random.random() < maxEDs_th:

                    i = n + (m_n - self.bestSF) * self.N
                    possible_schedules = np.where(self.delta[i][:])[0]

                    if possible_schedules.any():
                        random_timeslot = np.random.choice(possible_schedules) + timeshift
                        random_channel = np.random.choice(list(range(self.LRchannels)))

                        lora_schedules.append((n, m_n, random_timeslot, random_channel))
                        used_lora = True
                
                m_n += 1

            # or use LRFHSS CR1/3 or CR2/3 with 50/50 probability
            if not used_lora:
                m = np.random.choice([6,7])
                random_timeslot = np.random.randint(0, self.W - self.T_m[-1]) + timeshift
                lrfhss_scheduels.append((n, m, random_timeslot, 1))
        
        return lora_schedules, lrfhss_scheduels 
