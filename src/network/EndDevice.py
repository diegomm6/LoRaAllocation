from src.base import *

class EndDevice():

    def __init__(self, id_, lat, lon) -> None:
        
        self.nodeId = id_
        self.lat = lat
        self.lon = lon
        self.point = wgs84.latlon(self.lat, self.lon)

        # cached orbital dynamics data is updated whenever update_data is called
        self.cached_elevation = []
        self.cached_times = []
        self.cached_ranges = []
        self.cached_doppler_shifts = []
        self.cached_doppler_rates = []
        self.cached_availableSFs = []
        self.cached_bestSFs = []


    def fail_status(self, sf):

        fail_status = []
        rcvd_powers = [received_power(range_) for range_ in self.cached_ranges]
        for shift, rate, P_r in zip(self.cached_doppler_shifts, self.cached_doppler_rates, rcvd_powers):

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


    def generate_data(self, satname, t0, t1, slottime):
        
        elevation, times, ranges, shifts, rates = get_dopplereffect(satname, self.point, t0, t1, slottime)
        self.cached_elevation = elevation
        self.cached_times = times
        self.cached_ranges = ranges
        self.cached_doppler_shifts = shifts
        self.cached_doppler_rates = rates

        rcvd_powers = [received_power(range_) for range_ in ranges]
        self.cached_availableSFs = [get_available_sf(shift, rate, P_r) for shift, rate, P_r
                                    in zip(shifts, rates, rcvd_powers)]

        self.cached_bestSFs = [get_best_sf(availableSF) for availableSF in self.cached_availableSFs]
