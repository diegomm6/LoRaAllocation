from src.base import *
from src.network.EndDevice import EndDevice
from src.network.Gateway import Gateway
from src.mac.Scheduler import Scheduler
from src.mac.opt1Dmodel import Opt1DModel
from src.mac.opt2Dmodel import Opt2DModel
from src.mac.optLRFHSS import OptLRFHSS
from src.mac.lorawanClassA import LorawanClassA
from src.mac.JointMACDummyA import JointMACDummyA
from src.mac.JointMACDummyB import JointMACDummyB
from src.mac.JointMACDummyC import JointMACDummyC
from src.mac.DistributedUP import DistributedUplinkPolicy

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


    # for a given schedule calculate the distance at transmission
    # time for the corresponding end devices
    def get_distances_at_tx_time(self, schedules):

        distances_at_tx_time = []
        for n,m,p,q in schedules:
            ed: EndDevice = self.enddevices[n]
            distances_at_tx_time.append(ed.cached_ranges[p])

        return np.array(distances_at_tx_time)
    

    #########################################################################################
    #########################################################################################
    #########################################################################################

    def schedule_single_window(self, network_sizes, runs, range_based_order=False):

        samples = len(network_sizes)
        scheduled_txs = np.zeros((4, samples))
        successful_receptions = np.zeros((4, samples))
        support_time_all = np.zeros((4, samples, self.M))
        usage_time_all = np.zeros((4, samples, self.M))

        availableSF_data = np.array([ed.cached_availableSFs for ed in self.enddevices])
        availableSF_data = availableSF_data[:,:-1,:] # remove last timeslot

        if range_based_order:
            distances_at_beginning = [ed.cached_ranges[0] for ed in self.enddevices]
            sorted_indices = np.argsort(distances_at_beginning)
            availableSF_data = availableSF_data[sorted_indices]

        for i, numEDs in enumerate(network_sizes):

            sub_availableSF_data = availableSF_data[:numEDs]
            args = (numEDs, self.slottime, self.timeslots, self.numLRchannels, sub_availableSF_data)

            scheduler1D = Opt1DModel(*args)
            schedulerJointDummyA = JointMACDummyA(*args)
            schedulerJointDummyB = JointMACDummyB(*args)
            schedulerJointDummyC = JointMACDummyC(*args)

            # obtain optimal results only once
            schedules = scheduler1D.get_schedule()
            distances_at_tx_time = self.get_distances_at_tx_time(schedules)
            is_successful, sinr = self.gateway.calculate_sinr(schedules, distances_at_tx_time)
            scheduled_txs[0][i] = len(schedules) / numEDs
            successful_receptions[0][i] = is_successful.sum() / numEDs
            _, total_usage = scheduler1D.get_total_time_perSF(schedules)
            usage_time_all[0][i] = total_usage / (self.numLRchannels * self.timeslots)

            # obtain joint dummy results average
            for r in range(runs):

                lora_schedulesJointDummyA, _ = schedulerJointDummyA.get_schedule()
                distances_at_tx_time = self.get_distances_at_tx_time(lora_schedulesJointDummyA)
                is_successful, sinr = self.gateway.calculate_sinr(lora_schedulesJointDummyA, distances_at_tx_time)
                scheduled_txs[1][i] += len(lora_schedulesJointDummyA) / numEDs
                successful_receptions[1][i] += is_successful.sum() / numEDs
                _, total_usage = schedulerJointDummyA.get_total_time_perSF(lora_schedulesJointDummyA)
                usage_time_all[1][i] = total_usage / (self.numLRchannels * self.timeslots)

                lora_schedulesJointDummyB, _ = schedulerJointDummyB.get_schedule()
                distances_at_tx_time = self.get_distances_at_tx_time(lora_schedulesJointDummyB)
                is_successful, sinr = self.gateway.calculate_sinr(lora_schedulesJointDummyB, distances_at_tx_time)
                scheduled_txs[2][i] += len(lora_schedulesJointDummyB) / numEDs
                successful_receptions[2][i] += is_successful.sum() / numEDs
                _, total_usage = schedulerJointDummyB.get_total_time_perSF(lora_schedulesJointDummyB)
                usage_time_all[2][i] = total_usage / (self.numLRchannels * self.timeslots)

                lora_schedulesJointDummyC, _ = schedulerJointDummyC.get_schedule()
                distances_at_tx_time = self.get_distances_at_tx_time(lora_schedulesJointDummyC)
                is_successful, sinr = self.gateway.calculate_sinr(lora_schedulesJointDummyC, distances_at_tx_time)
                scheduled_txs[3][i] += len(lora_schedulesJointDummyC) / numEDs
                successful_receptions[3][i] += is_successful.sum() / numEDs
                _, total_usage = schedulerJointDummyC.get_total_time_perSF(lora_schedulesJointDummyC)
                usage_time_all[3][i] = total_usage / (self.numLRchannels * self.timeslots)

            del scheduler1D, schedulerJointDummyA, schedulerJointDummyB, schedulerJointDummyC
            
            print(f"done for {numEDs}")


        plt.figure(figsize=(10, 6))
        plt.plot(network_sizes, scheduled_txs[0], c=COLORS1[0], label='TX Opt1D')
        plt.plot(network_sizes, successful_receptions[0], c=COLORS1[0], linestyle='dashed', label='RX Opt1D')
        plt.plot(network_sizes, scheduled_txs[1] / runs, c=COLORS1[1], label='TX Dummy 50/50')
        plt.plot(network_sizes, successful_receptions[1] / runs, c=COLORS1[1], linestyle='dashed', label='RX Dummy 50/50')
        plt.plot(network_sizes, scheduled_txs[2] / runs, c=COLORS1[2], label='TX Best SF')
        plt.plot(network_sizes, successful_receptions[2] / runs, c=COLORS1[2], linestyle='dashed', label='RX Best SF')
        plt.plot(network_sizes, scheduled_txs[3] / runs, c=COLORS1[4], label='TX Sequential SF')
        plt.plot(network_sizes, successful_receptions[3] / runs, c=COLORS1[4], linestyle='dashed', label='RX Sequential SF')
        plt.xlabel('Generated LoRa packets')
        plt.ylabel('Ratio to created packets [%]')
        plt.title(f'Sent & Received LoRa packets per beacon')
        plt.legend()
        plt.grid()
        plt.show()
        plt.close()


        plt.figure(figsize=(10, 6))
        plt.plot(network_sizes, successful_receptions[0] / scheduled_txs[0], c=COLORS1[0], label='Opt1D')
        plt.plot(network_sizes, successful_receptions[1] / scheduled_txs[1], c=COLORS1[1], label='Dummy 50/50')
        plt.plot(network_sizes, successful_receptions[2] / scheduled_txs[2], c=COLORS1[2], label='Best SF')
        plt.plot(network_sizes, successful_receptions[3] / scheduled_txs[3], c=COLORS1[4], label='Sequential SF')
        plt.xlabel('Generated LoRa packets')
        plt.ylabel('PDR [%]')
        plt.title(f'Packet Delivery Ratio PDR')
        plt.legend()
        plt.grid()
        plt.show()
        plt.close()


        def plottime(m):
            plt.figure(figsize=(10, 6))
            plt.plot(network_sizes, usage_time_all[0,:,m], c=COLORS2[0], label=f'SF{m+7} Opt1D')
            plt.plot(network_sizes, usage_time_all[1,:,m], c=COLORS2[1], label=f'SF{m+7} Dummy 50/50')
            plt.plot(network_sizes, usage_time_all[2,:,m], c=COLORS2[2], label=f'SF{m+7} Best SF')
            plt.plot(network_sizes, usage_time_all[3,:,m], c=COLORS2[3], label=f'SF{m+7} Sequential SF')
            plt.xlabel('Number of EDs')
            plt.ylabel('Time ratio [%]')
            plt.title(f'Channel usage SF{m+7}')
            plt.legend()
            plt.grid()
            plt.show()
            plt.close()

        plottime(4)
        plottime(5)


    # get schduling results for a given scheduler, network size, uplink window
    def run_scheduler(self, SchedulerClass: Scheduler, numEDs, windowslots, availableSF_data, runs):

        usage_time_all = np.zeros(self.M)
        args = (numEDs, self.slottime, windowslots, self.numLRchannels, availableSF_data)
        scheduler : Scheduler = SchedulerClass(*args)

        scheduled_txs = 0
        successful_rxs = 0
        support_time_all = np.zeros(self.M)
        usage_time_all = np.zeros(self.M)

        for r in range(runs):

            schedules = scheduler.get_schedule()
            distances_at_tx_time = self.get_distances_at_tx_time(schedules)
            is_successful, sinr = self.gateway.calculate_sinr(schedules, distances_at_tx_time)
            _, total_usage = scheduler.get_total_time_perSF(schedules)

            scheduled_txs += len(schedules) / numEDs
            successful_rxs += is_successful.sum() / numEDs
            usage_time_all += total_usage / (self.numLRchannels * self.timeslots)

        del scheduler
        return scheduled_txs / runs, successful_rxs / runs, usage_time_all / runs


    #########################################################################################
    #########################################################################################
    #########################################################################################
    
    # solve the schdeuling for a given network size and scheduler
    # and solve for each uplink window sepparetely
    def schedule_multiple_window(self, network_size, uplink_period, runs, range_based_order=False):

        beacon_time = int(uplink_period / self.slottime)
        beacon_start = 0
        beacon_end = beacon_time
        numBeacons = self.timeslots // beacon_time

        with_coverage = np.zeros(numBeacons)
        scheduled_txs = np.zeros((4, numBeacons))
        successful_receptions = np.zeros((4, numBeacons))
        numTransmissions = np.zeros(network_size)

        availableSF_data = np.array([ed.cached_availableSFs for ed in self.enddevices])
        availableSF_data = availableSF_data[:,:-1,:] # remove last timeslot
        
        for b in range(numBeacons):

            print(f"beacon start: {beacon_start}, beacon end: {beacon_end}")

            if range_based_order:
                distances_at_beacon_start = [ed.cached_ranges[beacon_start] for ed in self.enddevices]
                sorted_indices = np.argsort(distances_at_beacon_start)
                availableSF_data = availableSF_data[sorted_indices]

            sub_availableSF_data = availableSF_data[:, beacon_start : beacon_end, :]
            args = (network_size, self.slottime, beacon_time, self.numLRchannels, sub_availableSF_data)

            scheduler1D = Opt1DModel(*args)
            schedulerJointDummyA = JointMACDummyA(*args)
            schedulerJointDummyB = JointMACDummyB(*args)
            schedulerJointDummyC = JointMACDummyC(*args)

            # obtain optimal results only once
            schedules = scheduler1D.get_schedule()
            distances_at_tx_time = self.get_distances_at_tx_time(schedules)
            is_successful, sinr = self.gateway.calculate_sinr(schedules, distances_at_tx_time)
            scheduled_txs[0][b] = len(schedules) / network_size
            successful_receptions[0][b] = is_successful.sum() / network_size

            with_coverage[b] = np.sum(scheduler1D.bestSF_n != -1)

            # obtain joint dummy results average
            for r in range(runs):

                lora_schedulesJointDummyA, _ = schedulerJointDummyA.get_schedule()
                distances_at_tx_time = self.get_distances_at_tx_time(lora_schedulesJointDummyA)
                is_successful, sinr = self.gateway.calculate_sinr(lora_schedulesJointDummyA, distances_at_tx_time)
                scheduled_txs[1][b] += len(lora_schedulesJointDummyA) / network_size
                successful_receptions[1][b] += is_successful.sum() / network_size

                lora_schedulesJointDummyB, _ = schedulerJointDummyB.get_schedule()
                distances_at_tx_time = self.get_distances_at_tx_time(lora_schedulesJointDummyB)
                is_successful, sinr = self.gateway.calculate_sinr(lora_schedulesJointDummyB, distances_at_tx_time)
                scheduled_txs[2][b] += len(lora_schedulesJointDummyB) / network_size
                successful_receptions[2][b] += is_successful.sum() / network_size

                lora_schedulesJointDummyC, _ = schedulerJointDummyC.get_schedule()
                distances_at_tx_time = self.get_distances_at_tx_time(lora_schedulesJointDummyC)
                is_successful, sinr = self.gateway.calculate_sinr(lora_schedulesJointDummyC, distances_at_tx_time)
                scheduled_txs[3][b] += len(lora_schedulesJointDummyC) / network_size
                successful_receptions[3][b] += is_successful.sum() / network_size

                numTransmissions = np.add(numTransmissions, schedulerJointDummyB.get_transmissions_per_ED(lora_schedulesJointDummyB))

            beacon_start = beacon_end
            beacon_end = beacon_start + beacon_time

            del scheduler1D, schedulerJointDummyA, schedulerJointDummyB, schedulerJointDummyC
            print(f"done for beacon {b}")


        plt.figure(figsize=(10, 6))
        plt.plot(range(numBeacons), with_coverage, c='k', label='EDs with coverage')
        plt.plot(range(numBeacons), scheduled_txs[0], c=COLORS1[0], label='TX Opt1D')
        plt.plot(range(numBeacons), successful_receptions[0], c=COLORS1[0], linestyle='dashed', label='RX Opt1D')
        plt.plot(range(numBeacons), scheduled_txs[1] / runs, c=COLORS1[1], label='TX Dummy 50/50')
        plt.plot(range(numBeacons), successful_receptions[1] / runs, c=COLORS1[1], linestyle='dashed', label='RX Dummy 50/50')
        plt.plot(range(numBeacons), scheduled_txs[2] / runs, c=COLORS1[2], label='TX Best SF')
        plt.plot(range(numBeacons), successful_receptions[2] / runs, c=COLORS1[2], linestyle='dashed', label='RX Best SF')
        plt.plot(range(numBeacons), scheduled_txs[3] / runs, c=COLORS1[4], label='TX Sequential SF')
        plt.plot(range(numBeacons), successful_receptions[3] / runs, c=COLORS1[4], linestyle='dashed', label='RX Sequential SF')
        plt.xlabel('beacon number')
        plt.ylabel('ratio to created packets [%]')
        plt.title(f'Sent & Received LoRa packets per beacon')
        plt.legend()
        plt.grid()
        plt.show()

        plt.close()

        if 0:
            numTransmissions /= runs
            # Count the frequency of each transmission count
            unique_counts, frequencies = np.unique(numTransmissions, return_counts=True)
            plt.figure(figsize=(8, 6))
            plt.bar(unique_counts, frequencies, color='skyblue', edgecolor='black')
            plt.xlabel('Number of Transmissions', fontsize=12)
            plt.ylabel('Number of Devices', fontsize=12)
            plt.title('Number of Devices per Transmission Count', fontsize=14)
            plt.xticks(unique_counts)
            plt.show()


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
        bounds = np.array([0,10,11,12,13,14]) # [0,7,8,9,10,11,12,13]
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
        cbar.ax.set_yticklabels(['0', 'SF10', 'SF11', 'SF12', 'LRFHSS'])
        
        plt.xlabel('Lap Time [seconds]')
        plt.ylabel('Device')
        plt.title('Visibility window with Best Data Rate per End Device')
        plt.show()
        #plt.savefig("img/visibilty_example2.jpg")


    def plot_heatmapSF_ULperiods(self, uplink_period, random_sample=False, eds_sample=1):

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
        
        plt.figure(figsize=(10, 6))
        
        colors_list = ['blue', 'cyan', 'yellowgreen', 'red']  # SF10, SF11, SF12, LRFHSS
        cmap = colors.ListedColormap(colors_list)
        
        # Updated bounds for SF10 (10), SF11 (11), SF12 (12), LRFHSS (13/14)
        bounds = [9.5, 10.5, 11.5, 12.5, 14.5]  # Added lower bound for SF10
        norm = colors.BoundaryNorm(bounds, len(colors_list))
        
        im = plt.imshow(plot_data, interpolation='none', 
                    extent=[0, laptime, 0, numDevices],
                    cmap=cmap, norm=norm, aspect='auto')
        
        cbar = plt.colorbar(im, ticks=[10, 11, 12, 13.5])  # Added SF10 tick
        cbar.set_label('DR', fontsize=12)
        cbar.ax.set_yticklabels(['SF10', 'SF11', 'SF12', 'LRFHSS'])  # Added SF10 label
        
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
        bounds = np.array([0,10,11,12,13,14]) # [0,7,8,9,10,11,12,13]
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
        cbar.ax.set_yticklabels(['0', 'SF10', 'SF11', 'SF12', 'LRFHSS'])

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
        anim.save('bestSF_test.gif', writer=writer)


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
