from src.base import *
from src.network.EndDevice import EndDevice
from src.network.Gateway import Gateway
from src.mac.Scheduler import Scheduler
from src.mac.opt1Dmodel import Opt1DModel
from src.mac.opt2Dmodel import Opt2DModel
from src.mac.optLRFHSS import OptLRFHSS
from src.mac.JointClassA import JointClassA
from src.mac.JointClassAValidSF import JointClassAValidSF
from src.mac.SuccessBased import SuccessBased
from src.mac.ALOHAmax import ALOHAmax


class DtSIoTNetwork():

    def __init__(self, constellation, numDevices, start_time, slottime, timeslots, numLRchannels,
                 numFHSSchannels, locationsfilename="locations.txt", datafile="",
                 save_cache=False) -> None:

        self.constellation = constellation
        self.numSatellites = len(self.constellation)
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

        # Create gateway for each satellite
        self.gateways = {}
        for satname in self.constellation:
            self.gateways[satname] = Gateway(satname, numDevices, slottime, timeslots, 
                                             numLRchannels, numFHSSchannels)
        
        self.initialize_data(datafile, save_cache)


    def load_scheduler_config(self, config):

        # success based sequental SF method with different Pmin thresholds
        labels1 = ["Opt1D", "$P_{min}=0.8$", "$P_{min}=0.6$", "$P_{min}=0.4$", "$P_{min}=0.2$"]
        scheduler_configs1 = [
            {'class': Opt1DModel, 'kwargs': {}},
            {'class': SuccessBased, 'kwargs': {'th': 0.8}},
            {'class': SuccessBased, 'kwargs': {'th': 0.6}},
            {'class': SuccessBased, 'kwargs': {'th': 0.4}},
            {'class': SuccessBased, 'kwargs': {'th': 0.2}}
        ]
    
        # different scheduling methods comparison for a single LoRa channel
        labels2 = ["Opt1D", "Joint-Class A", "Joint-Class A Valid-SF", "Success Best-SF",
                   "Success Seq-SF", "ALOHA Best-SF", "ALOHA Seq-SF"]
        scheduler_configs2 = [
            {'class': Opt1DModel, 'kwargs': {}},
            {'class': JointClassA, 'kwargs': {}},
            {'class': JointClassAValidSF, 'kwargs': {}},
            {'class': SuccessBased, 'kwargs': {'th': 0.6, 'SFmode': 0}},
            {'class': SuccessBased, 'kwargs': {'th': 0.6, 'SFmode': 1}},
            {'class': ALOHAmax, 'kwargs': {'SFmode': 0}},
            {'class': ALOHAmax, 'kwargs': {'SFmode': 1}}
        ]

        # different scheduling methods comparison for multiple LoRa channel
        labels3 = ["Opt1D", "Opt2D","Joint-Class A", "Joint-Class A Valid-SF", "Success Best-SF",
                   "Success Seq-SF", "ALOHA Best-SF", "ALOHA Seq-SF"]
        scheduler_configs3 = [
            {'class': Opt1DModel, 'kwargs': {}},
            {'class': Opt2DModel, 'kwargs': {}},
            {'class': JointClassA, 'kwargs': {}},
            {'class': JointClassAValidSF, 'kwargs': {}},
            {'class': SuccessBased, 'kwargs': {'th': 0.6, 'SFmode': 0}},
            {'class': SuccessBased, 'kwargs': {'th': 0.6, 'SFmode': 1}},
            {'class': ALOHAmax, 'kwargs': {'SFmode': 0}},
            {'class': ALOHAmax, 'kwargs': {'SFmode': 1}}
        ]

        if config==1:
            return scheduler_configs1, labels1, f'success_{self.numLRchannels}ch', COLORS2
        elif config==2:
            return scheduler_configs2, labels2, f'1d_{self.numLRchannels}ch_', COLORS3
        elif config==3:
            return scheduler_configs3, labels3, f'2d_{self.numLRchannels}ch_', COLORS4
        

    # for a given schedule calculate the distance at transmission
    # time from end devices to given satellite
    def get_distances_at_tx_time(self, schedules, satname):

        distances_at_tx_time = []
        for n, m, p, q in schedules:
            ed: EndDevice = self.enddevices[n]
            distances_at_tx_time.append(ed.cached_ranges[satname][p])
        return np.array(distances_at_tx_time)
    

    # Process successful receptions from all satellites.
    def process_rxs(self):

        # Collect all unique devices across all satellites
        all_devices = set()
        total_rxs = 0
        
        for satname in self.constellation:
            gateway: Gateway = self.gateways[satname]
            
            # Extract unique device IDs (n) from this satellite
            for (n, m, p, q) in gateway.successful_rxs:
                all_devices.add(n)

            total_rxs += len(gateway.successful_rxs)
        
        # Count unique devices across all satellites
        unique_rxs = len(all_devices)
        
        return unique_rxs, total_rxs
    

    # Get constellation-wide availableSF data for all devices.
    def get_constellation_availableSF(self):

        availableSF_data = np.array([ed.get_constellation_availableSF(self.constellation) 
                                    for ed in self.enddevices])
        
        return availableSF_data
    
    # Get constellation-wide bestSF data for all devices.
    def get_constellation_bestSF(self):

        bestSF_data = np.array([ed.get_constellation_bestSF(self.constellation) 
                                    for ed in self.enddevices])

        return bestSF_data
    
    # reset successful rx for all gateways
    def reset_gatways(self):
        for satname in self.constellation:
            gateway: Gateway = self.gateways[satname]
            gateway.successful_rxs = []


    #########################################################################################
    ##############################   SCHEDULING METHODS   ###################################
    #########################################################################################

    # Run scheduler with multi-satellite constellation support
    def run_scheduler(self, SchedulerClass, numEDs, windowslots, availableSF_data, runs,
                    timeshift=0, scheduler_kwargs={}):

        # Initialize scheduler (ONE scheduler for the whole constellation)
        args = (numEDs, self.slottime, windowslots, self.numLRchannels, availableSF_data)
        scheduler: Scheduler = SchedulerClass(*args, **scheduler_kwargs)
            
        # Tracking variables
        total_scheduled_txs = 0
        total_unique_rxs = 0
        total_successful_rxs = 0
        total_tx_per_sf = np.zeros(self.M)
        
        # Run multiple scheduling iterations
        for r in range(runs):
            # Create ONE schedule based on merged constellation availability
            schedules, _ = scheduler.get_schedule(timeshift)
            
            # EACH satellite independently calculates its receptions
            for satname in self.constellation:
                gateway: Gateway = self.gateways[satname]
                distances_at_tx_time = self.get_distances_at_tx_time(schedules, satname)
                gateway.compute_RXs(schedules, distances_at_tx_time)

            # Process receptions across the constellation
            unique_rxs, total_rxs = self.process_rxs()
            total_unique_rxs += unique_rxs
            total_successful_rxs += total_rxs
            total_scheduled_txs += len(schedules)

            # TX per sf m
            if schedules:
                schedules = np.array(schedules)
                m_values = schedules[:, 1].astype(int)
                tx_per_sf = np.bincount(m_values, minlength=self.M)
                total_tx_per_sf += tx_per_sf

            self.reset_gatways()
        
        # Clean up scheduler
        del scheduler

        # Compute averages
        avg_scheduled_txs = total_scheduled_txs / runs
        avg_successful_rxs = total_successful_rxs / runs
        avg_unique_rxs = total_unique_rxs / runs
        avg_tx_per_sf = total_tx_per_sf / runs

        return avg_scheduled_txs, avg_successful_rxs, avg_unique_rxs, avg_tx_per_sf



    # get resulst for a list of network sizes comparing differents schedulers
    def schedule_single_window(self, network_sizes, runs, config, range_based_order=False):

        scheduler_configs, labels, prefix, _colors = self.load_scheduler_config(config)
        num_methods = len(scheduler_configs)
        num_runs = [1] + [runs] * (num_methods - 1)  # Only Opt1DModel runs once

        samples = len(network_sizes)
        scheduled_txs = np.zeros((num_methods, samples))
        successful_rxs = np.zeros((num_methods, samples))
        unique_rxs = np.zeros((num_methods, samples))
        tx_per_sf = np.zeros((num_methods, samples, self.M))

        availableSF_data = self.get_constellation_availableSF()
        availableSF_data = availableSF_data[:, :-1, :]  # remove last timeslot

        if range_based_order:
            distances_at_beginning = [ed.cached_ranges[0] for ed in self.enddevices]
            sorted_indices = np.argsort(distances_at_beginning)
            availableSF_data = availableSF_data[sorted_indices]

        config_times = np.zeros((num_methods, samples))

        for i, numEDs in enumerate(network_sizes):
            print(f"running for {numEDs} EDs")

            for j in range(num_methods):
                t0 = time.perf_counter()
                config = scheduler_configs[j]
                args = (config['class'], numEDs, self.timeslots, availableSF_data[:numEDs], num_runs[j])

                scheduled_txs[j,i], successful_rxs[j,i], unique_rxs[j,i], tx_per_sf[j,i] = \
                    self.run_scheduler(*args, scheduler_kwargs=config['kwargs'])
                
                t1 = time.perf_counter()
                config_times[j,i] += (t1 - t0)

        for j in []:
            for i in range(samples):
                print(f"Total time for config {labels[j]} with {network_sizes[i]} EDs: {config_times[j,i]:.3f} s")


        simtime = self.timeslots * self.slottime
        single_window_plots(simtime, self.numSatellites, network_sizes, scheduled_txs, successful_rxs, \
                            unique_rxs, tx_per_sf, labels, prefix, _colors)
        

    # get resulst for a number of EDs comparing differents schedulers
    # and solve for each uplink window separately
    def schedule_multiple_window(self, numEDs, uplink_period, runs, config, range_based_order=False):

        scheduler_configs, labels, prefix, _colors = self.load_scheduler_config(config)
        beacon_time = int(uplink_period / self.slottime)
        beacon_start = 0
        beacon_end = beacon_time
        numBeacons = self.timeslots // beacon_time
        
        num_methods = len(scheduler_configs)
        num_runs = [1] + [runs] * (num_methods - 1)  # Only Opt1DModel runs once

        scheduled_txs = np.zeros((num_methods, numBeacons))
        total_rxs = np.zeros((num_methods, numBeacons))
        unique_rxs = np.zeros((num_methods, numBeacons))
        tx_per_sf = np.zeros((num_methods, numBeacons, self.M))

        availableSF_data = self.get_constellation_availableSF()
        availableSF_data = availableSF_data[:, :-1, :]  # remove last timeslot

        if range_based_order:
            distances_at_beginning = [ed.cached_ranges[0] for ed in self.enddevices]
            sorted_indices = np.argsort(distances_at_beginning)
            availableSF_data = availableSF_data[sorted_indices]

        config_times = [0.0] * num_methods

        for b in range(numBeacons):
            print(f"running for beacon {b}")
            sub_availableSF_data = availableSF_data[:, beacon_start : beacon_end, :]

            for j in range(num_methods):
                t0 = time.perf_counter()
                config = scheduler_configs[j]
                args = (config['class'], numEDs, beacon_time, sub_availableSF_data[:numEDs],\
                        num_runs[j], beacon_start)

                # Returns: scheduled_txs, total_rxs, unique_rxs
                scheduled_txs[j, b], total_rxs[j, b], unique_rxs[j, b], tx_per_sf[j, b] = \
                    self.run_scheduler(*args, scheduler_kwargs=config['kwargs'])
                
                t1 = time.perf_counter()
                config_times[j] += (t1 - t0)

            beacon_start = beacon_end
            beacon_end = beacon_start + beacon_time
        
        for j, total_t in enumerate(config_times):
            cfg_name = scheduler_configs[j].get('name', scheduler_configs[j]['class'].__name__)
            print(f"Total time for config {cfg_name} (index {j}): {total_t:.3f} s")

        beacon_results_plots(scheduled_txs, total_rxs, unique_rxs, tx_per_sf, labels, prefix, _colors)


    #########################################################################################
    ###############################  Simulation Data Methods  ###############################
    #########################################################################################

    # initialize constellation positions and end-device data for the simulation
    # either by generating new data or loading cached data
    def initialize_data(self, datafile, save_cache):

        if datafile:
            self.import_cache(datafile)
        else:
            for satname in self.constellation:
                gateway: Gateway = self.gateways[satname]
                gateway.generate_data(self.start_time, self.end_time)

                for ed in self.enddevices:
                    if ed.nodeId % 50 == 0: print(f"done for ED {ed.nodeId} on {satname}")
                    ed.generate_data(satname, self.start_time, self.end_time, self.slottime)
            
            if save_cache:
                self.export_cache()

    def export_cache(self):

        data = {"satellites": {}}
        
        # Export each satellite's data
        for satname in self.constellation:
            gateway: Gateway = self.gateways[satname]
            sim_timestamps = [t.isoformat() if hasattr(t, "isoformat") else t 
                             for t in gateway.cached_sat_times]
            
            data["satellites"][satname] = {
                "cached_sat_times": sim_timestamps,
                "cached_sat_lat": gateway.cached_sat_lat,
                "cached_sat_lon": gateway.cached_sat_lon,
            }
        
        # Export device data (per satellite)
        data["devices"] = []
        for ed in self.enddevices:
            device_data = {
                "nodeId": ed.nodeId,
                "lat": ed.lat,
                "lon": ed.lon,
                "satellites": {}
            }
            
            for satname in self.constellation:
                device_data["satellites"][satname] = {
                    "cached_elevation": ed.cached_elevation[satname],
                    "cached_ranges": ed.cached_ranges[satname],
                    "cached_doppler_shifts": ed.cached_doppler_shifts[satname],
                    "cached_doppler_rates": ed.cached_doppler_rates[satname].tolist(),
                    "cached_availableSFs": ed.cached_availableSFs[satname],
                    "cached_bestSFs": ed.cached_bestSFs[satname],
                }
            
            data["devices"].append(device_data)
        
        datafile = f"{self.numSatellites}sats_{self.numDevices}EDs_{self.timeslots}slots.json"
        with open(datafile, 'w') as file:
            json.dump(data, file)
        print(f"Cache saved to {datafile}")

    
    def import_cache(self, datafile):

        with open(datafile, 'r') as file:
            data = json.load(file)
        
        # Restore constellation data
        for satname in self.constellation:
            satellite_data = data["satellites"][satname]

            gateway: Gateway = self.gateways[satname]
            gateway.cached_sat_times = [datetime.fromisoformat(t) if isinstance(t, str) else t
                                         for t in satellite_data["cached_sat_times"]]
            gateway.cached_sat_lat = satellite_data["cached_sat_lat"]
            gateway.cached_sat_lon = satellite_data["cached_sat_lon"]
        
        # Restore device data
        for device_data in data["devices"]:
            ed: EndDevice = self.enddevices[device_data["nodeId"]]
            ed.lat = device_data["lat"]
            ed.lon = device_data["lon"]
            
            for satname in self.constellation:
                sat_data = device_data["satellites"][satname]
                ed.cached_elevation[satname] = sat_data["cached_elevation"]
                ed.cached_ranges[satname] = sat_data["cached_ranges"]
                ed.cached_times[satname] = self.gateways[satname].cached_sat_times
                ed.cached_doppler_shifts[satname] = sat_data["cached_doppler_shifts"]
                ed.cached_doppler_rates[satname] = np.array(sat_data["cached_doppler_rates"])
                ed.cached_availableSFs[satname] = sat_data["cached_availableSFs"]
                ed.cached_bestSFs[satname] = sat_data["cached_bestSFs"]
        
        self.data_cached = True


    #########################################################################################
    ###################################  Plotting Methods  ##################################
    #########################################################################################

    def plot_heatmapSF(self, random_sample=False, eds_sample=1):
        """
        Plot heatmap showing best SF across all satellites.
        For each device and timeslot, shows the optimal SF from ANY satellite.
        """
        cmap = plt.cm.rainbow
        bounds = np.array([0, 8, 9, 10, 11, 12, 13, 14])
        norm = colors.BoundaryNorm(bounds, cmap.N)
        
        numDevices = eds_sample if random_sample else self.numDevices
        device_sample = self.enddevices
        if random_sample:
            device_sample = random.sample(self.enddevices, numDevices)
        
        # Merge best SF from all satellites for each device
        constellation_bestSF = np.array([ed.get_constellation_bestSF(self.constellation) 
                                         for ed in device_sample])
        
        laptime = self.slottime * constellation_bestSF.shape[1]
        
        plt.figure(figsize=(12, 8))
        im = plt.imshow(constellation_bestSF, interpolation='none', 
                       extent=[0, laptime, 0, numDevices],
                       cmap=cmap, norm=norm, aspect='auto')
        
        tick_positions = (bounds[:-1] + bounds[1:]) / 2
        cbar = plt.colorbar(ticks=tick_positions)
        cbar.set_label('Best DR (Constellation)', fontsize=12)
        cbar.ax.tick_params(labelsize=12)
        cbar.ax.set_yticklabels(['No Coverage', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12', 'LRFHSS'])
        
        plt.xlabel('Time [seconds]', fontsize=14)
        plt.ylabel('Device ID', fontsize=14)
        plt.title(f'Constellation Visibility: Best DR per Device ({self.numSatellites} Satellites)', 
                  fontsize=16)
        plt.tight_layout()
        plt.show()
    

    def plot_heatmapSF_ULperiods(self, uplink_period, random_sample=False, eds_sample=1):
        """
        Plot heatmap showing best SF with uplink period divisions.
        Updated for multi-satellite constellation support.
        
        Parameters:
        -----------
        uplink_period : float
            Duration of uplink window in seconds
        random_sample : bool
            Whether to sample random devices
        eds_sample : int
            Number of devices to sample if random_sample=True
        """
        numDevices = eds_sample if random_sample else self.numDevices
        device_sample = self.enddevices
        if random_sample:
            device_sample = random.sample(self.enddevices, numDevices)

        # Get constellation-wide best SF for each device
        constellation_bestSF = np.array([ed.get_constellation_bestSF(self.constellation) 
                                        for ed in device_sample])
        
        laptime = self.slottime * constellation_bestSF.shape[1]
        
        # Convert zeros to NaN (transparent - no coverage)
        plot_data = constellation_bestSF.astype(float)
        plot_data[plot_data == 0] = np.nan


        plt.figure(figsize=(10, 6))

        # Color mapping: SF9=magenta, SF10=blue, SF11=cyan, SF12=yellowgreen, LRFHSS=red
        colors_list = ['magenta', 'blue', 'cyan', 'yellowgreen', 'red']
        cmap = colors.ListedColormap(colors_list)

        # Bounds for SF9 (9), SF10 (10), SF11 (11), SF12 (12), LRFHSS (13/14)
        bounds = [8.5, 9.5, 10.5, 11.5, 12.5, 14.5]
        norm = colors.BoundaryNorm(bounds, len(colors_list))

        im = plt.imshow(plot_data, interpolation='none', 
                    extent=[0, laptime, 0, numDevices],
                    cmap=cmap, norm=norm, aspect='auto')

        cbar = plt.colorbar(im, ticks=[9, 10, 11, 12, 13.5])
        cbar.set_label('Modulation Configuration', fontsize=18)
        cbar.ax.tick_params(labelsize=14)
        cbar.ax.set_yticklabels(['SF9', 'SF10', 'SF11', 'SF12', 'LR-FHSS'])

        # Add vertical lines for uplink phases
        num_beacons = int(laptime / uplink_period)
        for i in range(1, num_beacons):
            plt.axvline(x=i * uplink_period, color='black', linestyle='--', 
                    linewidth=1.5, alpha=0.6)
            
        beacon9_time = 8 * uplink_period
        plt.axvline(x=beacon9_time, color='black', linestyle='-', linewidth=2.5, alpha=0.9, zorder=10)
        
        plt.xlabel('Time [seconds]', fontsize=18)
        plt.ylabel('Device ID', fontsize=18)
        plt.xticks(fontsize=16)
        plt.yticks(fontsize=16)
        plt.title(f'Visibility Windows with lowest SF - '
                f'{self.numSatellites} Satellites', fontsize=20)
        
        # White background
        ax = plt.gca()
        ax.set_facecolor('white')
        
        plt.savefig(f"img/constellation_beacons_{len(self.constellation)}sats.pdf")
        plt.show()
        plt.close()


    def plot_bestSF_map(self):
        """
        Plot animated map showing best SF available from ANY satellite in constellation.
        Updated for multi-satellite support.
        """
        cmap = plt.cm.rainbow
        bounds = np.array([0, 9, 10, 11, 12, 13, 14])
        norm = colors.BoundaryNorm(bounds, cmap.N)
        tick_positions = (bounds[:-1] + bounds[1:]) / 2
        
        fig, ax = plt.subplots(figsize=(14, 10), subplot_kw={'projection': ccrs.Robinson()})
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS, linestyle=':')
        ax.gridlines(draw_labels=True)
        ax.set_extent([FR_E-8, FR_W+8, FR_S-8, FR_N+8], crs=ccrs.PlateCarree())
        
        # Device locations
        latitudes = np.array([ed.lat for ed in self.enddevices])
        longitudes = np.array([ed.lon for ed in self.enddevices])
        
        # Get constellation-wide best SF for each device
        constellation_bestSF = np.array([ed.get_constellation_bestSF(self.constellation) 
                                        for ed in self.enddevices])
        num_nodes, num_samples = constellation_bestSF.shape
        
        # Get times from first device
        times = self.enddevices[0].cached_times[self.constellation[0]]
        
        # Get satellite positions for all satellites
        sat_positions = {}
        for satname in self.constellation:
            gateway = self.gateways[satname]
            sat_positions[satname] = {
                'lat': gateway.cached_sat_lat,
                'lon': gateway.cached_sat_lon
            }
    
        # Define distinct colors/markers for different satellites
        sat_colors = ['magenta', 'cyan', 'yellow', 'lime', 'orange', 
                    'red', 'blue', 'green', 'purple']
        sat_markers = ['*', 'P', 'X', 'D', 's', '^', 'v', '<', '>']
        
        # Initial frame
        bestSF_per_node_attime = constellation_bestSF[:, 0]
        
        plt.title(f"Best DR (Constellation) at {times[0].strftime('%H:%M:%S')} - "
                f"{self.numSatellites} Satellites", fontsize=18)
        
        # Plot devices colored by best SF
        scatter = ax.scatter(longitudes, latitudes, c=bestSF_per_node_attime, 
                            cmap=cmap, norm=norm, s=50, 
                            transform=ccrs.PlateCarree(), zorder=5)
        
        # Plot all satellites
        sat_scatters = []
        for idx, satname in enumerate(self.constellation):
            sat_lat = sat_positions[satname]['lat'][0]
            sat_lon = sat_positions[satname]['lon'][0]
            color = sat_colors[idx % len(sat_colors)]
            marker = sat_markers[idx % len(sat_markers)]
            
            sat_scatter = ax.scatter(sat_lon, sat_lat, marker=marker, 
                                    color=color, s=200, edgecolors='black', linewidths=2,
                                    transform=ccrs.PlateCarree(), zorder=10,
                                    label=f'{satname[:12]}')  # Truncate long names
        
        # Colorbar
        cbar = plt.colorbar(scatter, ticks=tick_positions, pad=0.1)
        cbar.set_label('Best DR (from any satellite)', fontsize=12)
        cbar.ax.tick_params(labelsize=12)
        cbar.ax.set_yticklabels(['No Coverage', 'SF9', 'SF10', 'SF11', 'SF12', 'LRFHSS'])
        
        # Legend for satellites
        ax.legend(loc='lower left', fontsize=8, ncol=min(3, self.numSatellites))
        
        def update(frame):
            """Update function for animation"""
            ax.clear()
            ax.add_feature(cfeature.COASTLINE)
            ax.add_feature(cfeature.BORDERS, linestyle=':')
            ax.gridlines(draw_labels=True)
            ax.set_extent([FR_E-8, FR_W+8, FR_S-8, FR_N+8], crs=ccrs.PlateCarree())
            
            # Update best SF from constellation
            bestSF_per_node_attime = constellation_bestSF[:, frame]
            
            plt.title(f"Best DR (Constellation) at {times[frame].strftime('%H:%M:%S')} - "
                    f"{self.numSatellites} Satellites", fontsize=18)
            
            # Plot devices
            ax.scatter(longitudes, latitudes, c=bestSF_per_node_attime, 
                    cmap=cmap, norm=norm, s=50, 
                    transform=ccrs.PlateCarree(), zorder=5)
            
            # Plot all satellites at current frame
            for idx, satname in enumerate(self.constellation):
                sat_lat = sat_positions[satname]['lat'][frame]
                sat_lon = sat_positions[satname]['lon'][frame]
                color = sat_colors[idx % len(sat_colors)]
                marker = sat_markers[idx % len(sat_markers)]
                
                ax.scatter(sat_lon, sat_lat, marker=marker, 
                            color=color, s=200, edgecolors='black', linewidths=2,
                            transform=ccrs.PlateCarree(), zorder=10,
                            label=f'{satname[:12]}')
            
            # Add legend
            ax.legend(loc='lower left', fontsize=8, ncol=min(3, self.numSatellites))
            
            fig.canvas.draw()

        # Create animation
        anim = FuncAnimation(fig, update, frames=num_samples, interval=100)
        writer = PillowWriter(fps=30, metadata=dict(artist='Constellation Tracker'))

        # Save animation
        output_file = f'constellation_bestSF_{self.numSatellites}sats.gif'
        anim.save(output_file, writer=writer)
        print(f"✓ Animation saved as {output_file}")

        #plt.show()
        plt.close()
