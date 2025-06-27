from src.base import *

class Gateway:

    def __init__(self, numDevices, slottime, timeslots, numLRchannels,
                 numFHSSchannels) -> None:
        
        self.satellite = load_satellite()

        self.numDevices = numDevices
        self.slottime = slottime
        self.ToA_m = get_timeslots_perSF(slottime)
        self.timeslots = timeslots
        self.numLRchannels = numLRchannels
        self.numFHSSchannels = numFHSSchannels
        self.numSF = 6

        self.cached_sat_times = []
        self.cached_sat_lat = []
        self.cached_sat_lon = []

        # Small-scale fading
        #self.g_tx = np.random.exponential(scale=1.0, size=self.timeslots)


    def generate_data(self, t0, t1):

        t = t0
        while t < t1:
            sat = self.satellite.at(t)
            lat, lon = wgs84.latlon_of(sat)
            self.cached_sat_lat.append(lat.degrees)
            self.cached_sat_lon.append(lon.degrees)
            self.cached_sat_times.append(t.utc_datetime())
            t += timedelta(seconds=self.slottime)


    def calculate_outage_probability(self, schedules, distances):

        tx_data = []
        for i,p,q in schedules:
            n = i % self.numDevices
            m = i // self.numDevices
            tx_data.append((n,m,p,q))

        numTXs = len(tx_data)
        overlap_times = np.zeros((numTXs, numTXs))
        for tx1, (n1,m1,p1,q1) in enumerate(tx_data):
            for tx2, (n2,m2,p2,q2) in enumerate(tx_data[tx1:], start=tx1):

                overlap = calculate_overlap(p1, self.ToA_m[m1], p2, self.ToA_m[m2], self.slottime)
                overlap_times[tx1][tx2] = overlap
                overlap_times[tx2][tx1] = overlap

        # distance ratio matrix contain the ratio r[i] / r[j] for all i,j
        ratio_matrix = np.outer(distances, 1/distances)
        ratio_matrix = np.power(ratio_matrix, -ALPHA)

        P_cap = [] # capture probability for each transmission
        for tx1, (n1,m1,p1,q1) in enumerate(tx_data):

            exp_term = np.exp( -dBm2W(SINR_TH[m1]) * dBm2W(AWGN_VAR_DB) \
                              / (dBm2W(TX_POWER) * distances[tx1]**(-ALPHA)) )

            product = 1.0 
            for tx2, (n2,m2,p2,q2) in enumerate(tx_data):
                if tx2 != tx1:
                    product *= (1 / ( dBm2W(SINR_TH[m1]) * ratio_matrix[tx1][tx2] \
                                     * overlap_times[tx1][tx2] + 1))
            
            P_cap.append( exp_term * product)

        return P_cap


    def calcute_sinr(self, schedules, distances):

        r_alpha_tx = np.power(distances, -ALPHA)

        sinr_tx = np.zeros(len(schedules))
        is_successful = np.zeros(len(schedules))
        for tx1, (n1,m1,p1,q1) in enumerate(schedules):

            signal = np.random.exponential(scale=1.0) * r_alpha_tx[tx1]
            noise = dBm2W(AWGN_VAR_DB) / dBm2W(TX_POWER)
            interference = 0
            for tx2, (n2,m2,p2,q2) in enumerate(schedules):
                if tx2 != tx1:

                    overlap = calculate_overlap(p1, self.ToA_m[m1], p2, self.ToA_m[m2], self.slottime)
                    interference += np.random.exponential(scale=1.0) * r_alpha_tx[tx2] * (overlap / self.ToA_m[m2])

            sinr = signal / (interference + noise)
            sinr_tx[tx1] = mW2dBm(sinr)
            #print(mW2dBm(sinr_tx[tx1]*1e3))
            is_successful[tx1] = (sinr_tx[tx1] >= SINR_TH[m1])

        return is_successful, sinr_tx


    # simple sinr model considers path loss
    # collision only occurs if two tranmissions overlap in time, SF and channel
    def calculate_sinr(self, schedules, distances):

        rcvM = np.zeros((self.numLRchannels, self.numSF, self.timeslots))

        # fill received matrix rcvM, where m is the SF, p is the timeslot and q is the channel
        for n,m,p,q in schedules:
            rcvM[q, m, p : p+self.ToA_m[m]] += np.ones((self.ToA_m[m]))

        # print received matrix as heatmap for channel 0
        if 0 :
            heatmap = plt.imshow( rcvM[0], aspect='auto', cmap='hot', interpolation='nearest')
            plt.xlabel('Timeslots', fontsize=12)
            plt.ylabel('Spreading Factor (SF)', fontsize=12)
            plt.title('Concurrent Transmissions on Channel 0', fontsize=14)
            cbar = plt.colorbar(heatmap)
            cbar.set_label('Number of Concurrent Transmissions', fontsize=10)
            plt.yticks(ticks=np.arange(self.numSF), labels=[f'SF{7+i}' for i in range(self.numSF)])
            plt.tight_layout()
            plt.show()

        is_successful = np.zeros(len(schedules))
        collided = np.zeros(len(schedules))
        # given the time on air ToA_m for each SF, determine the collision status for each signal
        for tx1, (n1,m1,p1,q1) in enumerate(schedules):

            # if signal is not collided, calculate received power and compare with sensitivity
            if rcvM[q1][m1][p1 : p1+self.ToA_m[m1]].sum() == self.ToA_m[m1]:
 
                Pr = received_power(distances[tx1])
                is_successful[tx1] = (Pr >= LR_SENSITIVITY[m1])

            else:
                collided[tx1] = 1

        #print(f"\ncollided: {collided.sum()} of {len(schedules)}")
        #print(f"successful: {is_successful.sum()} of {len(schedules)}")

        return is_successful, 1


