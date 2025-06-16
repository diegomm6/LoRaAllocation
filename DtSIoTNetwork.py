from base import *
from EndDevice import EndDevice
from Gateway import Gateway
from matplotlib.animation import FuncAnimation, PillowWriter
from datetime import datetime
from Scheduler import Scheduler
from opt1Dmodel import Opt1DModel
from opt2Dmodel import Opt2DModel
from optLRFHSS import OptLRFHSS
from lorawanClassA import LorawanClassA
from DistributedUP import DistributedUplinkPolicy

class DtSIoTNetwork():

    def __init__(self, numDevices, start_time, slottime, timeslots, numLRchannels,
                 numFHSSchannels, locationsfilename="locations.txt", datafile="",
                 save_cache=False) -> None:

        self.numDevices = numDevices
        self.slottime = slottime
        self.start_time = start_time
        self.end_time = start_time + timedelta(seconds=(timeslots * slottime))
        self.timeslots = timeslots
        self.numLRchannels = numLRchannels
        self.numFHSSchannels = numFHSSchannels
        self.M = 6

        locations = read_locations(locationsfilename)
        self.enddevices = [EndDevice(i, lat, lon) for i, (lat, lon) in enumerate(locations)]
        self.enddevices = self.enddevices[:numDevices]

        self.gateway = Gateway(numDevices, slottime, timeslots, numLRchannels, numFHSSchannels)

        self.initialize_data(datafile, save_cache)



    #########################################################################################
    #########################################################################################
    #########################################################################################

    # run simulation for a list of networks sizes and provide metrics
    # against the number of EDs comparing SF allocation and time usage
    # for different methods, 1d, 2d and distributed
    def compare_methods(self, network_sizes, range_based_order=False):

        sf_colors = [u'#FF00FF', u'#00FF00', u'#00FFFF', u'#800080', u'#00CED1', u'#8c564b']
        samples = len(network_sizes)

        scheduled_txs = np.zeros((3, samples))
        successful_receptions = np.zeros((3, samples))

        availableSF_data = np.array([ed.cached_availableSFs for ed in self.enddevices])
        availableSF_data = availableSF_data[:,:-1,:-2] # remove last timeslot, remove lrfhss

        if range_based_order:
            distances_at_beginning = [ed.cached_ranges[0] for ed in self.enddevices]
            sorted_indices = np.argsort(distances_at_beginning)
            availableSF_data = availableSF_data[sorted_indices]


        for i, numEDs in enumerate(network_sizes):

            sub_availableSF_data = availableSF_data[:numEDs]

            args = (numEDs, self.slottime, self.timeslots, self.numLRchannels, sub_availableSF_data)

            scheduler1D = Opt1DModel(*args)
            scheduler2D = Opt2DModel(*args)
            lorawanClassA = LorawanClassA(*args)
            
            schedules = scheduler1D.get_schedule()
            distances_at_tx_time = self.get_distances_at_tx_time(schedules)
            is_successful, sinr = self.gateway.calcute_sinr(schedules, distances_at_tx_time)
            scheduled_txs[0][i] = len(schedules) / numEDs
            successful_receptions[0][i] = is_successful.sum() / numEDs

            schedules = scheduler2D.get_schedule()
            distances_at_tx_time = self.get_distances_at_tx_time(schedules)
            is_successful, sinr = self.gateway.calcute_sinr(schedules, distances_at_tx_time)
            scheduled_txs[1][i] = len(schedules) / numEDs
            successful_receptions[1][i] = is_successful.sum() / numEDs


            schedules = lorawanClassA.get_schedule()
            distances_at_tx_time = self.get_distances_at_tx_time(schedules)
            is_successful, sinr = self.gateway.calcute_sinr(schedules, distances_at_tx_time)
            scheduled_txs[2][i] = len(schedules) / numEDs
            successful_receptions[2][i] = is_successful.sum() / numEDs

            del scheduler1D, scheduler2D
            print(f"done for {numEDs}")


        plt.figure(figsize=(10, 6))

        plt.plot(network_sizes, scheduled_txs[0], c='b', label='Sent 1D')
        plt.plot(network_sizes, successful_receptions[0], c='b', linestyle='dashed', label='Received 1D')

        plt.plot(network_sizes, scheduled_txs[1], c='g', label='Sent 2D')
        plt.plot(network_sizes, successful_receptions[1], c='g', linestyle='dashed', label='Received 2D')

        plt.plot(network_sizes, scheduled_txs[2], c='r', label='Sent Class A')
        plt.plot(network_sizes, successful_receptions[2], c='r', linestyle='dashed', label='Received Class A')

        plt.xlabel('Generated packets')
        plt.ylabel('normalized packets')
        plt.title(f'Scheduling model for different network sizes')
        plt.legend()
        plt.grid()
        plt.show()

    #########################################################################################
    #########################################################################################
    #########################################################################################

    
    # run simulation for a list of networks sizes and provide metrics
    # against the number of EDs comparing SF allocation and time usage
    def run_simulation(self, network_sizes, solver="1D", range_based_order=False):

        sf_colors = [u'#FF00FF', u'#00FF00', u'#00FFFF', u'#800080', u'#00CED1', u'#8c564b']
        samples = len(network_sizes)

        no_coverage = np.zeros(samples)
        scheduled_txs = np.zeros(samples)
        successful_receptions = np.zeros(samples)
        tx_bestSF_all = np.zeros((samples, self.M))
        tx_otherSF_all = np.zeros((samples, self.M))
        support_time_all = np.zeros((samples, self.M))
        usage_time_all = np.zeros((samples, self.M))

        availableSF_data = np.array([ed.cached_availableSFs for ed in self.enddevices])
        availableSF_data = availableSF_data[:,:-1,:-2] # remove last timeslot, remove lrfhss

        if range_based_order:
            distances_at_beginning = [ed.cached_ranges[0] for ed in self.enddevices]
            sorted_indices = np.argsort(distances_at_beginning)
            availableSF_data = availableSF_data[sorted_indices]


        bestSF = self.M
        for i, numEDs in enumerate(network_sizes):

            sub_availableSF_data = availableSF_data[:numEDs]

            args = (numEDs, self.slottime, self.timeslots, self.numLRchannels, sub_availableSF_data)

            if solver == "1D": scheduler = Opt1DModel(*args)
            elif solver == "2D": scheduler = Opt2DModel(*args)
            else: return None

            schedules = scheduler.get_schedule()

            distances_at_tx_time = self.get_distances_at_tx_time(schedules)
            is_successful, sinr = self.gateway.calcute_sinr(schedules, distances_at_tx_time)
            no_coverage_EDs, _, tx_bestSF, tx_otherSF = scheduler.get_supported_EDs_perSF(schedules)

            no_coverage[i] = no_coverage_EDs / numEDs
            scheduled_txs[i] = len(schedules) / numEDs
            successful_receptions[i] = is_successful.sum() / numEDs

            tx_bestSF_all[i] = tx_bestSF / numEDs
            tx_otherSF_all[i] = tx_otherSF / numEDs

            support_time, total_usage = scheduler.get_total_time_perSF(schedules)
            support_time_all[i] = support_time / self.timeslots
            usage_time_all[i] = total_usage / (self.numLRchannels * self.timeslots)


            if scheduler.bestSF < bestSF:
                bestSF = scheduler.bestSF

            numTXs = len(sinr)
            y = np.arange(1, numTXs+1) / numTXs

            #plt.figure()
            #plt.plot(np.sort(sinr), y, marker='.', linestyle='-', label='Empirical CDF')
            #plt.xlabel('SINR (dB)')
            #plt.ylabel('Cumulative Probability')
            #plt.title('CDF of SINR Measurements')
            #plt.grid(True)
            #plt.legend()
            #plt.show()
            #plt.close()

            del scheduler
            print(f"done for {numEDs}")


        plt.figure(figsize=(10, 6))

        plt.plot(network_sizes, no_coverage, c='r', label='No coverage EDs')
        plt.plot(network_sizes, scheduled_txs, c='b', label='Scheduled TXs')
        plt.plot(network_sizes, successful_receptions, c='g', label='Successful RXs')

        for m in range(6):
            if np.any(tx_bestSF_all[:,m]) or np.any(tx_otherSF_all[:,m]):
                plt.plot(network_sizes, tx_bestSF_all[:,m], c=sf_colors[m-bestSF],
                         label=f'SF{m+7} as best')
                plt.plot(network_sizes, tx_otherSF_all[:,m], c=sf_colors[m-bestSF], 
                         linestyle='dashdot', label=f'SF{m+7} as alt')

        plt.xlabel('Number of EDs')
        plt.ylabel('device ratio [%]')
        plt.title(f'{solver} scheduling model for different network sizes')
        plt.legend()
        plt.grid()
        plt.show()

        plt.close()
        
        plt.figure(figsize=(10, 6))
        for m in range(6):
            if np.any(support_time_all[:,m]) or np.any(usage_time_all[:,m]):
                plt.plot(network_sizes, support_time_all[:,m], c=sf_colors[m-bestSF], 
                         label=f'support time SF{m+7}')
                plt.plot(network_sizes, usage_time_all[:,m], c=sf_colors[m-bestSF], 
                         linestyle='dashdot', label=f'usage time SF{m+7}')

        plt.xlabel('Number of EDs')
        plt.ylabel('time ratio [%]')
        plt.title(f'{solver} scheduling model SF allocation')
        plt.legend()
        plt.grid()
        plt.show()


    # solve the schdeuling for a given network size and scheduler
    # and solve for each uplink window sepparetely
    def solve_scheduling_per_beacon(self, network_size, beacon_time, solver="1D", range_based_order=False):

        sf_colors = [u'#FF00FF', u'#00FF00', u'#00FFFF', u'#800080', u'#00CED1', u'#8c564b']

        beacon_start = 0
        beacon_end = beacon_time
        numBeacons = self.timeslots // beacon_time

        no_coverage = np.zeros(numBeacons)
        scheduled_txs = np.zeros(numBeacons)
        successful_receptions = np.zeros(numBeacons)
        tx_bestSF_all = np.zeros((numBeacons, self.M))
        tx_otherSF_all = np.zeros((numBeacons, self.M))
        support_time_all = np.zeros((numBeacons, self.M))
        usage_time_all = np.zeros((numBeacons, self.M))

        numTransmissions = np.zeros(network_size)

        availableSF_data = np.array([ed.cached_availableSFs for ed in self.enddevices])
        availableSF_data = availableSF_data[:,:-1,:-2] # remove last timeslot, remove lrfhss
        
        bestSF = self.M
        for b in range(numBeacons):

            if range_based_order:
                distances_at_beacon_start = [ed.cached_ranges[beacon_start] for ed in self.enddevices]
                sorted_indices = np.argsort(distances_at_beacon_start)
                availableSF_data = availableSF_data[sorted_indices]

            sub_availableSF_data = availableSF_data[:network_size, beacon_start : beacon_end, :]
            args = (network_size, self.slottime, beacon_time, self.numLRchannels, sub_availableSF_data)

            if solver == "1D": scheduler = Opt1DModel(*args)
            elif solver == "2D": scheduler = Opt2DModel(*args)
            else: return None

            schedules = scheduler.get_schedule()

            distances_at_tx_time = self.get_distances_at_tx_time(schedules)
            is_successful = self.gateway.calcute_sinr(schedules, distances_at_tx_time)
            no_coverage_EDs, _, tx_bestSF, tx_otherSF = scheduler.get_supported_EDs_perSF(schedules)

            no_coverage[b] = no_coverage_EDs / network_size
            scheduled_txs[b] = len(schedules) / network_size
            successful_receptions[b] = is_successful.sum() / network_size

            tx_bestSF_all[b] = tx_bestSF / network_size
            tx_otherSF_all[b] = tx_otherSF / network_size

            support_time, total_usage = scheduler.get_total_time_perSF(schedules)
            support_time_all[b] = support_time / beacon_time
            usage_time_all[b] = total_usage / beacon_time

            numTransmissions = np.add(numTransmissions, scheduler.get_transmissions_per_ED(schedules))

            beacon_start = beacon_end
            beacon_end = beacon_start + beacon_time
            if scheduler.bestSF < bestSF:
                bestSF = scheduler.bestSF

            del scheduler
            print(f"done for beacon {b}")


        plt.figure(figsize=(10, 6))

        plt.plot(range(numBeacons), no_coverage, c='r', label='No coverage EDs')
        plt.plot(range(numBeacons), scheduled_txs, c='b', label='Scheduled TXs')
        plt.plot(range(numBeacons), successful_receptions, c='g', label='Successful RXs')

        for m in range(6):
            if np.any(tx_bestSF_all[:,m]) or np.any(tx_otherSF_all[:,m]):
                plt.plot(range(numBeacons), tx_bestSF_all[:,m], c=sf_colors[m-bestSF],
                         label=f'SF{m+7} as best')
                plt.plot(range(numBeacons), tx_otherSF_all[:,m], c=sf_colors[m-bestSF], 
                         linestyle='dashdot', label=f'SF{m+7} as alt')

        plt.xlabel('beacon number')
        plt.ylabel('device ratio [%]')
        plt.title(f'{solver} scheduling model for beacon (UL) period')
        plt.legend()
        plt.grid()
        plt.show()

        plt.close()

        plt.figure(figsize=(10, 6))
        for m in range(6):
            if np.any(support_time_all[:,m]) or np.any(usage_time_all[:,m]):
                plt.plot(range(numBeacons), support_time_all[:,m], c=sf_colors[m-bestSF], 
                         label=f'support time SF{m+7}')
                plt.plot(range(numBeacons), usage_time_all[:,m], c=sf_colors[m-bestSF], 
                         linestyle='dashdot', label=f'usage time SF{m+7}')

        plt.xlabel('beacon number')
        plt.ylabel('time ratio [%]')
        plt.title(f'{solver} scheduling model SF allocation')
        plt.legend()
        plt.grid()
        plt.show()

        plt.close()

        # Count the frequency of each transmission count
        unique_counts, frequencies = np.unique(numTransmissions, return_counts=True)

        # Create the bar plot
        plt.figure(figsize=(8, 6))
        plt.bar(unique_counts, frequencies, color='skyblue', edgecolor='black')

        # Add labels and title
        plt.xlabel('Number of Transmissions', fontsize=12)
        plt.ylabel('Number of Devices', fontsize=12)
        plt.title('Number of Devices per Transmission Count', fontsize=14)
        plt.xticks(unique_counts)

        # Show the plot
        plt.show()


    def solve_distributed_scheduling(self, network_size, beacon_time):

        sf_colors = [u'#FF00FF', u'#00FF00', u'#00FFFF', u'#800080', u'#00CED1', u'#8c564b']

        beacon_start = 0
        beacon_end = beacon_time
        numBeacons = self.timeslots // beacon_time

        no_coverage = np.zeros(numBeacons)
        scheduled_txs = np.zeros(numBeacons)
        collisions = np.zeros(numBeacons)
        tx_bestSF_all = np.zeros((numBeacons, self.M))
        tx_otherSF_all = np.zeros((numBeacons, self.M))
        support_time_all = np.zeros((numBeacons, self.M))
        usage_time_all = np.zeros((numBeacons, self.M))

        availableSF_data = np.array([ed.cached_availableSFs for ed in self.enddevices])
        availableSF_data = availableSF_data[:,:-1,:-2] # remove last timeslot, remove lrfhss

        bestSF = self.M
        for b in range(numBeacons):

            sub_availableSF_data = availableSF_data[:network_size, beacon_start : beacon_end, :]
            args = (network_size, self.slottime, beacon_time, self.numLRchannels, sub_availableSF_data)

            scheduler = DistributedUplinkPolicy(*args)
            scheduler.set_data(numBeacons, beacon_time)
            schedules = scheduler.get_schedule(b, beacon_start, beacon_end)

            distances_at_tx_time = self.get_distances_at_tx_time(schedules)
            is_successful = self.gateway.calcute_sinr(schedules, distances_at_tx_time)
            no_coverage_EDs, _, tx_bestSF, tx_otherSF = scheduler.get_supported_EDs_perSF(schedules)

            no_coverage[b] = no_coverage_EDs / network_size
            scheduled_txs[b] = len(schedules) / network_size
            collisions[b] = scheduler.get_collisions(schedules)  / network_size

            tx_bestSF_all[b] = tx_bestSF / network_size
            tx_otherSF_all[b] = tx_otherSF / network_size

            support_time, total_usage = scheduler.get_total_time_perSF(schedules)
            support_time_all[b] = support_time / beacon_time
            usage_time_all[b] = total_usage / beacon_time

            beacon_start = beacon_end
            beacon_end = beacon_start + beacon_time
            if scheduler.bestSF < bestSF:
                bestSF = scheduler.bestSF

            del scheduler


        plt.figure(figsize=(10, 6))

        plt.plot(range(numBeacons), no_coverage, c='r', label='No coverage EDs')
        plt.plot(range(numBeacons), scheduled_txs, c='b', label='Scheduled TXs')
        plt.plot(range(numBeacons), collisions, c='m', label='collisions')

        for m in range(6):
            if np.any(tx_bestSF_all[:,m]) or np.any(tx_otherSF_all[:,m]):
                plt.plot(range(numBeacons), tx_bestSF_all[:,m], c=sf_colors[m-bestSF],
                         label=f'SF{m+7} as best')
                plt.plot(range(numBeacons), tx_otherSF_all[:,m], c=sf_colors[m-bestSF], 
                         linestyle='dashdot', label=f'SF{m+7} as alt')

        plt.xlabel('beacon number')
        plt.ylabel('device ratio [%]')
        plt.title('distributed model for beacon (UL) period')
        plt.legend()
        plt.grid()
        plt.show()

        plt.close()

        plt.figure(figsize=(10, 6))
        for m in range(6):
            if np.any(support_time_all[:,m]) or np.any(usage_time_all[:,m]):
                plt.plot(range(numBeacons), support_time_all[:,m], c=sf_colors[m-bestSF], 
                         label=f'support time SF{m+7}')
                plt.plot(range(numBeacons), usage_time_all[:,m], c=sf_colors[m-bestSF], 
                         linestyle='dashdot', label=f'usage time SF{m+7}')

        plt.xlabel('beacon number')
        plt.ylabel('time ratio [%]')
        plt.title('distributed scheduling model SF allocation')
        plt.legend()
        plt.grid()
        plt.show()
    

    def solve_scheduling(self, solver):
        
        availableSF_data = np.array([ed.cached_availableSFs for ed in self.enddevices])
        args = (self.numDevices, self.slottime, self.timeslots, self.numLRchannels, availableSF_data)

        if solver == "1D":            self.scheduler = Opt1DModel(*args)
        elif solver == "2D":          self.scheduler = Opt2DModel(*args)
        elif solver == "distributed": self.scheduler = DistributedUplinkPolicy(*args)
        elif solver == "lrfhss":      self.scheduler = OptLRFHSS(self.numDevices, self.slottime, self.timeslots,
                                                                 self.numFHSSchannels, availableSF_data)
        else: return None
        

        schedules = self.scheduler.get_schedule()

        #self.scheduler.plot_ed_vs_time(schedules)
        #self.scheduler.plot_sf_vs_time(schedules)
        #self.scheduler.plot_txs_per_channel(schedules)

        #prob = self.calculate_outage_probability(schedules)
        #self.scheduler.plot_transmissions_sf_status(schedules)

        self.scheduler.plot_txs_per_channel_lrfhss(schedules)
        self.scheduler.write_schedule(schedules)

        #distances_at_tx_time = self.get_distances_at_tx_time(schedules)
        #is_successful = self.gateway.calcute_sinr(schedules, distances_at_tx_time)
        #print(f"{is_successful.sum()} successful receptions out of {len(schedules)} transmissions")


    # for a given schedule calculate the distance at transmission
    # time for the corresponding end devices
    def get_distances_at_tx_time(self, schedules):

        distances_at_tx_time = []
        for i,p,q in schedules:
            n = i % self.numDevices
            ed: EndDevice = self.enddevices[n]
            distances_at_tx_time.append(ed.cached_ranges[p])

        return np.array(distances_at_tx_time)


    ###########################################################################
    ########################  Simulation Data Methods  ########################
    ###########################################################################


    # initialize satellite positions and end-device data for the simulation
    # either by generating new data or loading cached data
    def initialize_data(self, datafile, save_cache):

        if datafile:
            self.import_cache(datafile)

        else:
            self.gateway.generate_data(self.start_time, self.end_time)
            for ed in self.enddevices:
                ed.generate_data(self.start_time, self.end_time, self.slottime)
                
            if save_cache:
                self.export_cache()


    # Exports the cached data
    def export_cache(self):

        sim_timestamps = [t.isoformat() if hasattr(t, "isoformat") else t for t in self.gateway.cached_sat_times]

        data = {
            "satellite": {
                "cached_sat_times": sim_timestamps,
                "cached_sat_lat": self.gateway.cached_sat_lat,
                "cached_sat_lon": self.gateway.cached_sat_lon,
            },
            "devices": []
        }

        for ed in self.enddevices:
            device_data = {
                "nodeId": ed.nodeId,
                "lat": ed.lat,
                "lon": ed.lon,
                "cached_elevation": ed.cached_elevation,
                "cached_ranges": ed.cached_ranges,
                "cached_doppler_shifts": ed.cached_doppler_shifts,
                "cached_doppler_rates": ed.cached_doppler_rates.tolist(),
                "cached_availableSFs": ed.cached_availableSFs,
                "cached_bestSFs": ed.cached_bestSFs,
            }
            data["devices"].append(device_data)

        datafile = f"data_{self.numDevices}EDs_{self.timeslots}slots.json"
        with open(datafile, 'w') as file:
            json.dump(data, file)


    def import_cache(self, datafile):

        with open(datafile, 'r') as file:
            data = json.load(file)

        # Restore satellite data
        satellite_data = data["satellite"]
        self.gateway.cached_sat_times = [datetime.fromisoformat(t) if isinstance(t, str) else t 
                                 for t in satellite_data["cached_sat_times"]]
        self.gateway.cached_sat_lat = satellite_data["cached_sat_lat"]
        self.gateway.cached_sat_lon = satellite_data["cached_sat_lon"]

        # Restore device data using direct index access
        ed : EndDevice
        for device_data in data["devices"]:
            ed = self.enddevices[device_data["nodeId"]]  # Direct index access
            ed.lat = device_data["lat"]
            ed.lon = device_data["lon"]
            ed.cached_elevation = device_data["cached_elevation"]
            ed.cached_ranges = device_data["cached_ranges"]
            ed.cached_times = self.gateway.cached_sat_times
            ed.cached_doppler_shifts = device_data["cached_doppler_shifts"]
            ed.cached_doppler_rates = np.array(device_data["cached_doppler_rates"])
            ed.cached_availableSFs = device_data["cached_availableSFs"]
            ed.cached_bestSFs = device_data["cached_bestSFs"]

        self.data_cached = True


    ###########################################################################
    ############################  Plotting Methods  ###########################
    ###########################################################################

    def plot_bestSF_ocurrences(self):

        bestSF_per_node = np.array([ed.cached_bestSFs for ed in self.enddevices])
        times = self.enddevices[0].cached_times

        num_nodes, num_samples = bestSF_per_node.shape
        count_matrix = np.zeros((6, num_samples), dtype=int)
    
        for sf in range(7, 13):
            count_matrix[sf-7] = np.sum(bestSF_per_node == sf, axis=0)

        plt.figure(figsize=(12, 8))

        for sf in range(7, 13):
            plt.plot(times, count_matrix[sf-7], label=f'SF{sf}')

        plt.title(f'Best SF ocurrences for {num_nodes} end-devices', fontsize=16)
        plt.xlabel('Time', fontsize=14)
        plt.ylabel('Ocurrences [devices]', fontsize=14)
        plt.legend()
        plt.grid()
        plt.tight_layout()
        plt.show()
        #plt.savefig("img/ocurrences.pdf")


    def plot_availabeSF(self):

        availableSF = np.array(self.enddevices[0].cached_availableSFs[:-1])
        laptime = self.slottime * availableSF.shape[0]

        plt.figure(figsize=(10, 6))
        im = plt.imshow(availableSF.T, interpolation='none', aspect='auto',
                        extent=[0, laptime, 12.5, 6.5])

        plt.xlabel('Lap Time [seconds]')
        plt.ylabel('SF')
        plt.yticks(ticks=[12, 11, 10, 9, 8, 7])
        plt.title('Available SFs for a random ED')
        plt.show()
        #plt.savefig("img/availableSF_example.jpg")



    def plot_heatmapSF(self, random_sample=False, eds_sample=1):
        
        cmap = plt.cm.rainbow
        bounds = np.array([0,11,12,13,14]) # [0,7,8,9,10,11,12,13]
        norm = colors.BoundaryNorm(bounds, cmap.N)
        numDevices = self.numDevices

        # random sample
        if random_sample:
            numDevices = eds_sample
            device_sample = random.sample(self.enddevices, numDevices)
            bestSF_per_node = np.array([ed.cached_bestSFs for ed in device_sample])
        # all EDs
        else:
            bestSF_per_node = np.array([ed.cached_bestSFs for ed in self.enddevices])

        # trim between first rise time until last set time
        non_zero_cols = ~np.all(bestSF_per_node == 0, axis=0)
        #filtered_SF = bestSF_per_node[:, non_zero_cols]
        filtered_SF = bestSF_per_node

        laptime = self.slottime * bestSF_per_node.shape[1]

        plt.figure(figsize=(10, 6))
        im = plt.imshow(np.array(filtered_SF), interpolation='none', extent=[0, laptime, 0, numDevices], 
                        cmap=cmap, norm=norm, aspect='auto')
        tick_positions = (bounds[:-1] + bounds[1:]) / 2

        cbar = plt.colorbar(ticks=tick_positions)
        cbar.set_label('DR', fontsize=12)
        cbar.ax.tick_params(labelsize=12)
        #cbar.ax.set_yticklabels([str(int(tick)) for tick in bounds[:-1]])
        cbar.ax.set_yticklabels(['0', 'SF11', 'SF12', 'LRFHSS'])
        
        plt.xlabel('Lap Time [seconds]')
        plt.ylabel('Device')
        plt.title('Visibility window with Best Data Rate per End Device')
        plt.show()
        #plt.savefig("img/visibilty_example2.jpg")


    def plot_heatmapSF_ULperiods(self, uplink_period, random_sample=False, eds_sample=1):

        # Get the data
        numDevices = self.numDevices
        if random_sample:
            numDevices = eds_sample
            device_sample = random.sample(self.enddevices, numDevices)
            bestSF_per_node = np.array([ed.cached_bestSFs for ed in device_sample])
        else:
            bestSF_per_node = np.array([ed.cached_bestSFs for ed in self.enddevices])
        
        laptime = self.slottime * bestSF_per_node.shape[1]
        
        # Convert zeros to NaN (which will be transparent in the plot)
        plot_data = bestSF_per_node.astype(float)  # Convert to float to use NaN
        plot_data[plot_data == 0] = np.nan
        
        # Set up the figure with white background
        plt.figure(figsize=(10, 6))
        
        # Create a colormap for SF11, SF12, LRFHSS
        colors_list = ['cyan', 'yellowgreen', 'red']  # Colors for SF11, SF12, LRFHSS
        cmap = colors.ListedColormap(colors_list)
        
        # Create bounds for values 11, 12, 13/14
        bounds = [10.5, 11.5, 12.5, 14.5]
        norm = colors.BoundaryNorm(bounds, len(colors_list))
        
        # Plot the data (zeros are NaN and will be transparent)
        im = plt.imshow(plot_data, interpolation='none', 
                    extent=[0, laptime, 0, numDevices],
                    cmap=cmap, norm=norm, aspect='auto')
        
        # Create the colorbar with correct labels
        cbar = plt.colorbar(im, ticks=[11, 12, 13.5])
        cbar.set_label('DR', fontsize=12)
        cbar.ax.set_yticklabels(['SF11', 'SF12', 'LRFHSS'])
        
        # Add vertical lines for uplink phases
        for i in range(1, int(laptime / uplink_period)):
            plt.axvline(x=i * uplink_period, color='black', linestyle='--')
        
        plt.xlabel('Lap Time [seconds]')
        plt.ylabel('Device')
        plt.title('Visibility window with Best Data Rate per End Device')
        
        # Make sure the background is white
        ax = plt.gca()
        ax.set_facecolor('white')
        
        plt.show()



    def plot_bestSF_map(self):

        cmap = plt.cm.rainbow
        bounds = np.array([0,11,12,13,14]) # [0,7,8,9,10,11,12,13]
        norm = colors.BoundaryNorm(bounds, cmap.N)
        tick_positions = (bounds[:-1] + bounds[1:]) / 2

        fig, ax = plt.subplots(figsize=(12, 10), subplot_kw={'projection': ccrs.Robinson()})
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS, linestyle=':')
        ax.gridlines(draw_labels=True)
        ax.set_extent([FR_E-8, FR_W+8, FR_S-8, FR_N+8], crs=ccrs.PlateCarree())

        latitudes = np.array([ed.lat for ed in self.enddevices])
        longitudes = np.array([ed.lon for ed in self.enddevices])
        bestSF_per_node = np.array([ed.cached_bestSFs for ed in self.enddevices])
        num_nodes, num_samples = bestSF_per_node.shape

        times = self.enddevices[0].cached_times
        bestSF_per_node_attime = bestSF_per_node[:, 0]
        current_sat_lat = self.gateway.cached_sat_lat[0]
        current_sat_lon = self.gateway.cached_sat_lon[0]

        plt.title(f"Best DR at time {times[0].strftime('%H:%M:%S')}", fontsize=18)

        scatter = ax.scatter(longitudes, latitudes, c=bestSF_per_node_attime, cmap=cmap, norm=norm, s=50, transform=ccrs.PlateCarree())
        ax.scatter(current_sat_lon, current_sat_lat, marker='*', color='magenta', s=70, transform=ccrs.PlateCarree(), label='Satellite')

        cbar = plt.colorbar(scatter, ticks=tick_positions, pad=0.1)
        cbar.set_label('DR', fontsize=12)
        cbar.ax.tick_params(labelsize=12)
        #cbar.ax.set_yticklabels([str(int(tick)) for tick in bounds[:-1]])
        cbar.ax.set_yticklabels(['0', 'SF11', 'SF12', 'LRFHSS'])

        def update(frame):

            ax.clear()
            ax.add_feature(cfeature.COASTLINE)
            ax.add_feature(cfeature.BORDERS, linestyle=':')
            ax.gridlines(draw_labels=True)
            ax.set_extent([FR_E-8, FR_W+8, FR_S-8, FR_N+8], crs=ccrs.PlateCarree())

            bestSF_per_node_attime = bestSF_per_node[:, frame]
            current_sat_lat = self.gateway.cached_sat_lat[frame]
            current_sat_lon = self.gateway.cached_sat_lon[frame]

            plt.title(f"Best DR at time {times[frame].strftime('%H:%M:%S')}", fontsize=18)

            ax.scatter(longitudes, latitudes, c=bestSF_per_node_attime, cmap=cmap, norm=norm, s=50, transform=ccrs.PlateCarree())
            ax.scatter(current_sat_lon, current_sat_lat, marker='*', color='magenta', s=80, transform=ccrs.PlateCarree(), label='Satellite')

            fig.canvas.draw()

    
        anim = FuncAnimation(fig, update, frames=num_samples, interval=1)
        writer = PillowWriter(fps=10, metadata=dict(artist='Me'))

        #plt.show()
        anim.save('bestSF2.gif', writer=writer)

    def plot_heatmapSF_ULperiods(self, uplink_period, random_sample=False, eds_sample=1):

        # Get the data
        numDevices = self.numDevices
        if random_sample:
            numDevices = eds_sample
            device_sample = random.sample(self.enddevices, numDevices)
            bestSF_per_node = np.array([ed.cached_bestSFs for ed in device_sample])
        else:
            bestSF_per_node = np.array([ed.cached_bestSFs for ed in self.enddevices])
        
        laptime = self.slottime * bestSF_per_node.shape[1]
        
        # Convert zeros to NaN (which will be transparent in the plot)
        plot_data = bestSF_per_node.astype(float)  # Convert to float to use NaN
        plot_data[plot_data == 0] = np.nan
        
        # Set up the figure with white background
        plt.figure(figsize=(10, 6))
        
        # Create a colormap for SF11, SF12, LRFHSS
        colors_list = ['cyan', 'yellowgreen', 'red']  # Colors for SF11, SF12, LRFHSS
        cmap = colors.ListedColormap(colors_list)
        
        # Create bounds for values 11, 12, 13/14
        bounds = [10.5, 11.5, 12.5, 14.5]
        norm = colors.BoundaryNorm(bounds, len(colors_list))
        
        # Plot the data (zeros are NaN and will be transparent)
        im = plt.imshow(plot_data, interpolation='none', 
                    extent=[0, laptime, 0, numDevices],
                    cmap=cmap, norm=norm, aspect='auto')
        
        # Create the colorbar with correct labels
        cbar = plt.colorbar(im, ticks=[11, 12, 13.5])
        cbar.set_label('DR', fontsize=12)
        cbar.ax.set_yticklabels(['SF11', 'SF12', 'LRFHSS'])
        
        # Add vertical lines for uplink phases
        for i in range(1, int(laptime / uplink_period)):
            plt.axvline(x=i * uplink_period, color='black', linestyle='--')
        
        plt.xlabel('Lap Time [seconds]')
        plt.ylabel('Device')
        plt.title('Visibility window with Best Data Rate per End Device')
        
        # Make sure the background is white
        ax = plt.gca()
        ax.set_facecolor('white')
        
        plt.show()


    def plot_availableSF_map(self, sf):

        cmap = plt.cm.rainbow
        bounds = np.array([0,1,2,3,4,5]) # [0,7,8,9,10,11,12,13]
        norm = colors.BoundaryNorm(bounds, cmap.N)
        tick_positions = (bounds[:-1] + bounds[1:]) / 2

        fig, ax = plt.subplots(figsize=(12, 10), subplot_kw={'projection': ccrs.Robinson()})
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS, linestyle=':')
        ax.gridlines(draw_labels=True)
        ax.set_extent([FR_E-8, FR_W+8, FR_S-8, FR_N+8], crs=ccrs.PlateCarree())

        latitudes = np.array([ed.lat for ed in self.enddevices])
        longitudes = np.array([ed.lon for ed in self.enddevices])

        # obtain the status of each node at each time
        # possible status are: succes, failure due to doppler shift,
        # failure due to doppler rate, failure due to both doppler shift and rate
        # and failure due to range
        fail_status = np.array([ed.fail_status(sf) for ed in self.enddevices])
                               
        num_nodes, num_samples = fail_status.shape

        times = self.enddevices[0].cached_times
        fail_status_per_node_attime = fail_status[:, 0]
        current_sat_lat = self.gateway.cached_sat_lat[0]
        current_sat_lon = self.gateway.cached_sat_lon[0]

        plt.title(f"SF{sf} status at time {times[0].strftime('%H:%M:%S')}", fontsize=18)

        scatter = ax.scatter(longitudes, latitudes, c=fail_status_per_node_attime, cmap=cmap, norm=norm, s=50, transform=ccrs.PlateCarree())
        ax.scatter(current_sat_lon, current_sat_lat, marker='*', color='magenta', s=70, transform=ccrs.PlateCarree(), label='Satellite')

        cbar = plt.colorbar(scatter, ticks=tick_positions, pad=0.1)
        cbar.set_label('DR', fontsize=12)
        cbar.ax.tick_params(labelsize=12)
        #cbar.ax.set_yticklabels([str(int(tick)) for tick in bounds[:-1]])
        cbar.ax.set_yticklabels(['Success', 'No link', 'Rate & Shift Fail', 'Rate failure','Shift fail'])

        def update(frame):

            ax.clear()
            ax.add_feature(cfeature.COASTLINE)
            ax.add_feature(cfeature.BORDERS, linestyle=':')
            ax.gridlines(draw_labels=True)
            ax.set_extent([FR_E-8, FR_W+8, FR_S-8, FR_N+8], crs=ccrs.PlateCarree())

            fail_status_per_node_attime = fail_status[:, frame]
            current_sat_lat = self.gateway.cached_sat_lat[frame]
            current_sat_lon = self.gateway.cached_sat_lon[frame]

            plt.title(f"SF{sf} status at time {times[frame].strftime('%H:%M:%S')}", fontsize=18)

            ax.scatter(longitudes, latitudes, c=fail_status_per_node_attime, cmap=cmap, norm=norm, s=50, transform=ccrs.PlateCarree())
            ax.scatter(current_sat_lon, current_sat_lat, marker='*', color='magenta', s=80, transform=ccrs.PlateCarree(), label='Satellite')

            fig.canvas.draw()

    
        anim = FuncAnimation(fig, update, frames=num_samples, interval=1)
        writer = PillowWriter(fps=10, metadata=dict(artist='Me'))

        #plt.show()
        anim.save(f'SF{sf}_status.gif', writer=writer)
