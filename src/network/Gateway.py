from src.base import *

class Gateway:

    def __init__(self, satname, numDevices, slottime, timeslots, numLRchannels, numFHSSchannels) -> None:
        
        self.satellite = load_satellite(satname)

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

        self.successful_rxs = []

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


    # compute successful receptions
    # collision only occurs if two tranmissions overlap in time, SF and channel
    def compute_RXs(self, schedules, distances):

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

        # given the time on air ToA_m for each SF, determine the collision status for each signal
        for tx1, (n1,m1,p1,q1) in enumerate(schedules):

            # if signal is not collided, calculate received power and compare with sensitivity
            if rcvM[q1][m1][p1 : p1+self.ToA_m[m1]].sum() == self.ToA_m[m1]:
 
                Pr = received_power(distances[tx1])
                if Pr >= LR_SENSITIVITY[m1]:
                    self.successful_rxs.append((n1,m1,p1,q1))

