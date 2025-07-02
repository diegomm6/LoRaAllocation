from src.base import *

# schdeuler module to assign transmission time slots and channels
# to ED in the network owning this module
class Scheduler():

    def __init__(self, numDevices, slottime, timeslots, numLRchannels, availableSF_data) -> None:

        self.N = numDevices                 # number of EDs
        self.M = 6                          # number of LoRa SFs
        self.C = 2                          # number of LR-FHSS CRs
        self.W = timeslots                  # number of time slots
        self.LRchannels = numLRchannels     # number of LoRa channels
        self.FHSSchannels = 1
        self.slottime = slottime            # seconds per time slot 

        self.T_m = get_timeslots_perSF(slottime) # time on air per SF in slots
        self.T_c = get_timeslots_perCR(slottime) # time on air per CR in slots

        self.availableSF_per_node = availableSF_data
        self.bestSF = self.get_bestSF_overall()

        #network.plot_heatmapSF(numDevices, t0, t1, self.slottime, False)
        #network.plot_availabeSF(t0, t1, self.slottime)

        self.delta = self.get_delta()
        self.bestSF_n = self.get_best_SF_per_ed()

        self.xi_p_q = np.zeros((self.W, self.LRchannels), dtype=object)
        self.xi_p_q_m = np.zeros((self.W, self.LRchannels, self.M - self.bestSF), dtype=object)

        for p in range(self.W):
            for q in range(self.LRchannels):

                self.xi_p_q[p][q] = self.get_xi(p,q)

                for m in range(self.M - self.bestSF):
                    self.xi_p_q_m[p][q][m] = self.get_xi_m(p,q,m)



    # get schedule method must be implemented in derived classes
    def get_schedule(self):
        raise NotImplementedError()
    

    def get_bestSF_overall(self):

        bestSF_overall = 15 # means no sf or cr coverage
        for m in reversed(range(self.M)):
            if np.any(self.availableSF_per_node[:,:,m]): # any node any time
                bestSF_overall = m

        return bestSF_overall


    # delta = 1 if SF m is available for ED n at time t
    # The packet is available if SF m is supported 
    # for all t' in [t, t+w(m)] and if t+w(m) < t_end
    def get_delta_perED(self, n, m, t):

        can_finish = t + self.T_m[m] <= self.W
        if not can_finish: return False
        
        packet_slots = self.availableSF_per_node[n, t : t + self.T_m[m], m]

        return np.all(packet_slots == 1) 


    def get_delta(self):

        delta = np.zeros(((self.M - self.bestSF) * self.N, self.W))

        for m in range(self.M - self.bestSF):
            for n in range(self.N):
                for p in range(self.W):

                    i = n + m*self.N
                    delta[i][p] = self.get_delta_perED(n, m + self.bestSF, p)

        return delta


    # return a list of tuples (i,a,b) where i is an item and (a,b)
    # is a position, such that if i is placed in (a,b) it covers
    # the point (p,q) while finishing before the frame ends
    def get_combinations_at_timeslost(self, a, p, q):

        perslot_combinations = []
        for m in range(self.M - self.bestSF):

            toa = self.T_m[m + self.bestSF]
            if (a + toa <= self.W) and (p < a + toa):
                perslot_combinations += [(n + m*self.N, a, q) for n in range(self.N)]
        
        return perslot_combinations


    # set of all possible (i,a,b) such that 
    # if i is placed in (a,b) it covers point (p,q)
    def get_xi(self, p, q):

        total_combinations = []
        t_prime = p
        while t_prime >= 0 and t_prime > (p - self.T_m[-1]):

            total_combinations += self.get_combinations_at_timeslost(t_prime, p, q)
            t_prime -= 1

        return total_combinations


    # set of all possible (i,a,b) such that 
    # if i is placed in (a,b) it covers point (p,q)
    # only for a given SF m
    def get_xi_m(self, p, q, m):

        total_combinations = []
        t_prime = p
        while t_prime >= 0 and t_prime > (p - self.T_m[-1]):

            toa = self.T_m[m + self.bestSF]
            if (t_prime + toa <= self.W) and (p < t_prime + toa):
                total_combinations += [(i + m*self.N, t_prime, q) for i in range(self.N)]

            t_prime -= 1

        return total_combinations
    

    # best SF supported for each ed given delta status
    def get_best_SF_per_ed(self):
        
        bestSF_achieved_per_node = np.full(self.N, -1)
        
        for n in range(self.N):
            for m in range(self.M - self.bestSF):

                i = n + m*self.N
                if np.any(self.delta[i]):
                    bestSF_achieved_per_node[n] = m+self.bestSF
                    break  # Found the lowest SF that works, move to next ed
        
        return bestSF_achieved_per_node
    
    
    ###########################################################################
    #######################  Solution Analysis Methods  #######################
    ###########################################################################

    # calculat total time each SF is supported from the availableSF_per_node
    # and the total time each SF is used from the schedules
    def get_total_time_perSF(self, schedules):
        
        transmissions = np.zeros((self.LRchannels, self.M, self.W))
        for n,m,p,q in schedules:
            transmissions[q, m, p: p + self.T_m[m]] += 1

        any_device_support = np.max(self.availableSF_per_node, axis=0)
        sf_total_support = np.count_nonzero(any_device_support, axis=0)

        # total usage time without considering collision as more usage
        filtered_txs = transmissions.copy()
        filtered_txs[filtered_txs > 1] = 1

        sf_total_usage = np.sum(filtered_txs, axis=(0, 2))

        return sf_total_support , sf_total_usage


    def get_supported_EDs_perSF(self, schedules):
    
        bestSF_achieved_per_node = self.bestSF_n
        no_coverage_EDs = np.sum(bestSF_achieved_per_node == -1)
        competing_EDd_m = [np.sum(bestSF_achieved_per_node == m) for m in range(self.M)]

        transmitted_with_bestSF = np.zeros(self.M)
        transmitted_with_otherSF = np.zeros(self.M)

        for n,m,p,q in schedules:
            if m == bestSF_achieved_per_node[n]:
                transmitted_with_bestSF[m] += 1
            else:
                transmitted_with_otherSF[m] += 1

        return no_coverage_EDs, competing_EDd_m, transmitted_with_bestSF, transmitted_with_otherSF


    # calculate collision for distributed model
    def get_collisions(self, schedules):

        collisions = 0
        transmissions = np.zeros((self.LRchannels, self.M, self.W))
        for n,m,p,q in schedules:
            toa = self.T_m[m]
            transmissions[q, m, p: p + toa] += 1

            if np.sum(transmissions[q, m, p: p + toa]) > toa:
                collisions += 1 

        return collisions
    

    def get_transmissions_per_ED(self, schedules):

        numTransmissions = np.zeros(self.N)
        for n,m,p,q in schedules:
            numTransmissions[n] += 1

        return numTransmissions

    ###########################################################################
    #####################  Solution Visualization Methods  ####################
    ###########################################################################

    # get decoded tranmissions after capture probability
    def plot_transmissions_sf_status(self, schedules):

        bestSF_achieved_per_node = self.bestSF_n
        no_coverage_EDs = np.sum(bestSF_achieved_per_node == -1)
        competing_EDd_m = [np.sum(bestSF_achieved_per_node == m) for m in range(self.M)]

        transmitted_with_bestSF = np.zeros(self.M)
        transmitted_with_otherSF = np.zeros(self.M)

        for n,m,p,q in schedules:

            if m == bestSF_achieved_per_node[n]:
                transmitted_with_bestSF[m] += 1
            else:
                transmitted_with_otherSF[m] += 1

        print(f"Number of EDs with no coverage: {no_coverage_EDs}\n")
        
        for m in range(self.M):
            if competing_EDd_m[m] == 0: continue

            numSlots_m = int(self.W / self.T_m[m]) * self.LRchannels

            print(f"SF{m+7} : competing EDs {competing_EDd_m[m]}")
            print(f"max transmissions supported: {numSlots_m}")
            print(f"transmitted with best SF {transmitted_with_bestSF[m]}")
            print(f"transmitted with other SF {transmitted_with_otherSF[m]}\n")


    # plot number of transmissions per channel over time
    def plot_txs_per_channel(self, schedules):

        laptime = self.slottime * self.W
        _time = np.arange(0, laptime, self.slottime)
        txs_per_channel = [0] * self.LRchannels
        transmissions = np.zeros((self.LRchannels, self.M, self.W))

        for n,m,p,q in schedules:

            #print(f"ED {n} SF {7+m} at time {p} on channel {q}")
            # Fill the schedule array for this device
            transmissions[q, m, p: p + self.T_m[m]] += 1
            txs_per_channel[q] += 1

        numTXs = np.sum(transmissions, axis=0)

        plt.figure(figsize=(10, 6))
        for m in range(self.M):
            if np.sum(numTXs[m]) == 0: continue
            plt.plot(_time, numTXs[m,:], label=f'SF {7+m}')

        plt.plot(_time, np.sum(numTXs, axis=0), label='Total', color='k')
        plt.xlabel('Lap Time [seconds]')
        plt.ylabel('number of transmissions')
        plt.title('Number of transmissions across all channels')
        plt.legend()
        plt.grid()
        plt.show()


    # plot number of transmissions per channel over time
    def plot_txs_per_channel_lrfhss(self, schedules):

        laptime = self.slottime * self.W
        _time = np.arange(0, laptime, self.slottime)
        txs_per_channel = [0] * self.FHSSchannels
        transmissions = np.zeros((self.FHSSchannels, self.C, self.W))

        for n,c,p,q in schedules:

            #print(f"ED {n} CR{c}/3 at time {p} on channel {q}")
            transmissions[q, c, p: p + self.T_c[c]] += 1
            txs_per_channel[q] += 1

        numTXs = np.sum(transmissions, axis=0)

        plt.figure(figsize=(10, 6))
        for c in range(self.C):
            if np.sum(numTXs[c]) == 0: continue

            label = f'CR {c}/3' if c else f'CR 2/3'
            plt.plot(_time, numTXs[c,:], label=label)

        plt.plot(_time, np.sum(numTXs, axis=0), label='Total', linestyle='dotted', color='k')
        plt.xlabel('Lap Time [seconds]')
        plt.ylabel('number of transmissions')
        plt.title('Number of transmissions across all channels')
        plt.legend()
        plt.grid()
        plt.show()


    # plot solution for each SF over time for all channels
    def plot_ed_vs_time(self, schedules):

        cmap = plt.cm.rainbow
        bounds = np.array([0,7,8,9,10,11,12,13]) #np.arange(6, 14)
        tick_positions = (bounds[:-1] + bounds[1:]) / 2
        norm = colors.BoundaryNorm(bounds, cmap.N)
        laptime = self.slottime * self.W

        txs_per_channel = [0] * self.LRchannels
        transmissions = np.zeros((self.LRchannels, self.N, self.W))

        for n,m,p,q in schedules:

            #print(f"ED {n} sf {7+m} at time {p} in channel {q}")
            # Fill the schedule array for this device
            transmissions[q, n, p: p + self.T_m[m]] = 7+m
            txs_per_channel[q] += 1


        for ch in range(self.LRchannels):
            print(f"Channel {ch} has {txs_per_channel[ch]} EDs transmitting")

            plt.figure(figsize=(10, 6))
            im = plt.imshow(np.array(transmissions[ch]), interpolation='none', extent=[0, laptime, 0, self.N], 
                            cmap=cmap, norm=norm, aspect='auto')

            cbar = plt.colorbar(ticks=tick_positions)
            cbar.set_label('SF', fontsize=12)
            cbar.ax.tick_params(labelsize=12)
            cbar.ax.set_yticklabels([str(int(tick)) for tick in bounds[:-1]])

            plt.xlabel('Lap Time [seconds]')
            plt.ylabel('Device')
            plt.title(f'{txs_per_channel[ch]} EDs transmitting in Channel {ch}')
            plt.show()
            #plt.savefig("img/solution.jpg")

    
    def plot_sf_vs_time(self, schedules):

        laptime = self.slottime * self.W
        txs_per_channel = [0] * self.LRchannels
        transmissions = np.zeros((self.LRchannels, self.M, self.W))

        for n,m,p,q in schedules:

            #print(f"ED {n} SF {7+m} at time {p} on channel {q}")
            # Fill the schedule array for this device
            transmissions[q, m, p: p + self.T_m[m]] += 1
            txs_per_channel[q] += 1

        for ch in range(self.LRchannels):
            print(f"Channel {ch} has {txs_per_channel[ch]} EDs transmitting")

            plt.figure(figsize=(10, 6))
            im = plt.imshow(np.array(transmissions[ch]), interpolation='none', extent=[0, laptime, 0, self.M], 
                            origin='lower', aspect='auto')

            # Set y-ticks positions at the center of each cell and add a shift of 7
            yticks_positions = np.arange(0, self.M) + 0.5
            yticks_labels = np.arange(7, 7 + self.M)
            plt.yticks(yticks_positions, yticks_labels)

            cbar = plt.colorbar(im)
            cbar.set_label('Number of Transmissions')

            plt.xlabel('Lap Time [seconds]')
            plt.ylabel('Spreading Factor')
            plt.title(f'{txs_per_channel[ch]} EDs transmitting in Channel {ch}')
            plt.show()
            #plt.savefig("img/solution.jpg")




    # plot solution for each SF over time
    # considers the multiple channels in subplot
    def plot_txs_multichannel(self, schedules):

        cmap = plt.cm.rainbow
        bounds = np.array([0, 7, 8, 9, 10, 11, 12, 13])  # Define color boundaries
        norm = colors.BoundaryNorm(bounds, cmap.N)

        # Extract pairs and initialize schedules for each device
        pairs = [(n, m, p, q) for (n, m, p, q), _ in schedules.items()]
        transmissions = [np.zeros(self.W) for _ in range(self.N)]


        # Fill schedules based on transmissions
        for n, m, p, q in pairs:

            #print(f"ED {n} sf {7+m} at time {p} on channel {q}")
            for t in range(p, p + self.T_m[m]):
                transmissions[n][t] = 7 + m

        laptime = self.slottime * self.W

        # Extract unique channel IDs
        channels = sorted(set(q for _,_,_, q in pairs))

        # Create subplots for each channel
        fig, axs = plt.subplots(self.H, 1, figsize=(10, 6 * self.H), squeeze=False)

        for idx, channel in enumerate(channels):
            ax = axs[idx][0]
            
            # Filter schedules specific to the current channel
            filtered_schedules = [np.where(np.array(transmissions[device]) == channel + 7,
                                            transmissions[device], 0) 
                                for device in range(self.N)]
            
            im = ax.imshow(
                np.array(filtered_schedules), interpolation='none', extent=[0, laptime, 0, self.N],
                cmap=cmap, norm=norm, aspect='auto'
            )
            
            tick_positions = (bounds[:-1] + bounds[1:]) / 2
            cbar = fig.colorbar(im, ax=ax, ticks=tick_positions)
            cbar.set_label('SF', fontsize=12)
            cbar.ax.tick_params(labelsize=12)
            cbar.ax.set_yticklabels([str(int(tick)) for tick in bounds[:-1]])

            ax.set_xlabel('Lap Time [seconds]')
            ax.set_ylabel('Device')
            ax.set_title(f'Channel {channel}: {len(pairs)} EDs Transmitting')

        plt.tight_layout()
        plt.show()

        #plt.savefig("img/solution_2dmodel.jpg")

