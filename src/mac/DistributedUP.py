from src.base import *
from src.mac.Scheduler import Scheduler

class DistributedUplinkPolicy(Scheduler):

    def __init__(self, numDevices, slottime, timeslots, numLRchannels, availableSF_data) -> None:
        super().__init__(numDevices, slottime, timeslots, numLRchannels, availableSF_data)

    
    # slotted ALOHA game threshold
    def get_threshold_m(self, numNodes, numSlots):

        # multiple channels 
        numSlots *= self.LRchannels

        a = 1
        if numNodes==0: return a

        b = 1 - (1/numSlots)
        if numNodes > (-1 / np.log(b)):
            a = -1 / (numNodes * np.log(b))

        return a
    

    # calculate number of nodes achieving each SF as its
    # best for each beacon and the SA Game Threshold
    def get_competitors_and_th(self, numBeacons, beacon_time):

        competitors_b_m = np.zeros((numBeacons, self.M - self.bestSF))
        th_b_m = np.ones((numBeacons, self.M - self.bestSF))

        for b in range(numBeacons):
            for m in range(self.M - self.bestSF):
                competitors_b_m[b][m] = np.sum(self.bestSF_n_b[:][b] == m+self.bestSF)

                numSlots = beacon_time / self.T_m[m+self.bestSF]
                th_b_m[b][m] = self.get_threshold_m(competitors_b_m[b][m], numSlots)

        return competitors_b_m, th_b_m


    # best sf per node per beacon
    def get_bestSF_per_beacon(self, numBeacons, beacon_time):

        bestSF_n_b = np.full((self.N, numBeacons), -1)
        start = 0

        for n in range(self.N):
            for b in range(numBeacons):

                for m in range(self.M - self.bestSF):
                    i = n + m*self.N
                    if np.any(self.delta[i][start : start + beacon_time]):
                        bestSF_n_b[n][b] = m+self.bestSF
                        break  # Found the lowest SF that works, move to next node
                
                start += beacon_time
        
        return bestSF_n_b
    

    def set_data(self, numBeacons, beacon_time):
        self.bestSF_n = self.get_best_SF_per_ed()
        self.bestSF_n_b = self.get_bestSF_per_beacon(numBeacons, beacon_time)
        self.competitors_b_m, self.th_b_m = self.get_competitors_and_th(numBeacons, beacon_time)
    

    def get_schedule(self, b, beacon_start, beacon_end):

        lora_schedules = self.uplink_schedules(b, beacon_start, beacon_end)
        return lora_schedules
    

    def uplink_schedules(self, b, beacon_start, beacon_end):

        # m_n_b: best SF for ED n durgin frame b
        # m_n_B: best SF for ED n durgin satellite pass (B frames)

        lora_schedules = []
        fhss_devices = []
        for n in range(self.N):
            
            m_n_b = self.bestSF_n_b[n][b]
            # skip nodes without link support
            if m_n_b == -1: continue
            
            m_n_b -= self.bestSF
            i = n + m_n_b*self.N

            # transmist using SF
            if random.uniform(0,1) < self.th_b_m[b][m_n_b]:

                possible_schedules = np.where(self.delta[i][beacon_start : beacon_end])[0]
                random_timeslot = np.random.choice(possible_schedules)
                random_channel = np.random.choice(list(range(self.LRchannels)))
                lora_schedules.append((i, random_timeslot, random_channel))

            #transmit using fhss
            else: 
                fhss_devices.append(n)

        return lora_schedules
