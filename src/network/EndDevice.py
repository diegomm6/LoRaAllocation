from src.base import *

class EndDevice():

    def __init__(self, id_, lat, lon) -> None:
        
        self.nodeId = id_
        self.lat = lat
        self.lon = lon
        self.point = wgs84.latlon(self.lat, self.lon)

        # cached orbital dynamics data is updated whenever update_data is called
        self.cached_elevation = {}
        self.cached_times = {}
        self.cached_ranges = {}
        self.cached_doppler_shifts = {}
        self.cached_doppler_rates = {}
        self.cached_availableSFs = {}
        self.cached_bestSFs = {}


    def generate_data(self, satname, t0, t1, slottime):
        """Generate data for a specific satellite"""
        elevation, times, ranges, shifts, rates = get_dopplereffect(satname, self.point, t0, t1, slottime)
        
        self.cached_elevation[satname] = elevation
        self.cached_times[satname] = times
        self.cached_ranges[satname] = ranges
        self.cached_doppler_shifts[satname] = shifts
        self.cached_doppler_rates[satname] = rates
        
        rcvd_powers = [received_power(range_) for range_ in ranges]
        self.cached_availableSFs[satname] = [get_available_sf(shift, rate, P_r) 
                                              for shift, rate, P_r in zip(shifts, rates, rcvd_powers)]
        self.cached_bestSFs[satname] = [get_best_sf(availableSF) 
                                         for availableSF in self.cached_availableSFs[satname]]
    
    
    def get_constellation_bestSF(self, satnames):
        """
        Merge best SF from multiple satellites.
        For each timeslot, return the best SF available from any satellite.
        """
        num_timeslots = len(self.cached_bestSFs[satnames[0]])
        constellation_bestSF = []
        
        for t in range(num_timeslots):
            sf_options = []
            for satname in satnames:
                sf = self.cached_bestSFs[satname][t]
                if sf > 0:  # Valid SF
                    sf_options.append(sf)
            
            # Choose best (lowest SF = highest data rate)
            constellation_bestSF.append(min(sf_options) if sf_options else 0)
        
        return constellation_bestSF
    

    def get_constellation_availableSF(self, satnames):
        """
        Merge availableSF data from multiple satellites.
        For each timeslot, returns which SFs are available from ANY satellite.

        Returns np.array : shape (num_timeslots, num_SFs)
        Binary array where [t, sf] = 1 if SF is available at timeslot t from any satellite
        """
        num_timeslots = len(self.cached_availableSFs[satnames[0]])
        num_SFs = len(self.cached_availableSFs[satnames[0]][0])  # (typically 6)
        
        # Initialize constellation availability array
        constellation_availableSF = np.zeros((num_timeslots, num_SFs), dtype=int)
        
        for t in range(num_timeslots):
            # For each timeslot, merge availability from all satellites
            for satname in satnames:
                # Get available SFs for this satellite at this timeslot
                available_sfs = self.cached_availableSFs[satname][t]
                
                # OR operation: if ANY satellite has SF available, mark as available
                constellation_availableSF[t] = np.logical_or(
                    constellation_availableSF[t], 
                    available_sfs
                ).astype(int)
        
        return constellation_availableSF



    def fail_status(self, sf, satname):
        """Get failure status for a specific satellite"""
        fail_status = []
        rcvd_powers = [received_power(range_) for range_ in self.cached_ranges[satname]]
        
        for shift, rate, P_r in zip(self.cached_doppler_shifts[satname], 
                                     self.cached_doppler_rates[satname], 
                                     rcvd_powers):
            if not linkbudget_success(P_r, sf):
                fail_status.append(1)
                continue
            if not doppler_shift_success(shift, sf) and not doppler_rate_success(rate, sf):
                fail_status.append(2)
                continue
            if doppler_shift_success(shift, sf) and not doppler_rate_success(rate, sf):
                fail_status.append(3)
                continue
            if not doppler_shift_success(shift, sf) and doppler_rate_success(rate, sf):
                fail_status.append(4)
                continue
            fail_status.append(0)
        
        return fail_status
