from src.base import *

class LoRaTransmission():

    def __init__(self, _id: int, node_id: int, startSlot: int,
                 payload_size: int, sf: int, channel: int, duration: int) -> None:

        self._id = _id
        self.node_id = node_id
        self.startSlot = startSlot
        self.payload_size = payload_size
        self.channel = channel
        self.sf = sf
        self.duration = duration
    
    def __lt__(self, other) -> bool:
        return self.startSlot < other.startSlot
    

class LoRaNode():

    def __init__(self, id_, minEangle, simTimeslots, timeslot) -> None:

        self.timeslot = timeslot
        self.simTimeslots = simTimeslots

        maxRange = dist2sat_angle(minEangle)
        maxGround_dist = EARTH_R * np.arcsin( maxRange*np.cos(minEangle) / (EARTH_R+SAT_H) )

        self.nodeId = id_
        self.ground_dist = maxGround_dist * np.sqrt(random.uniform(0, 1))
        self.b_angle = random.uniform(0, 2*np.pi)

        self.x = self.ground_dist * np.cos(self.b_angle)
        self.y = self.ground_dist * np.sin(self.b_angle)

        self.TXtime = -self.y / SAT_V
        self.maxE_angle = np.arctan( SAT_H / abs(self.x) )

        doppler_data = doppler(self.maxE_angle, self.TXtime)
        self.doppler_shift = doppler_data[0]  
        self.doppler_rate = doppler_data[1]
        
        self.visibility = (self.y + np.sqrt(maxGround_dist**2 - self.x**2)) / SAT_V


    def get_transmissions(self) -> list[LoRaTransmission]:

        sf = random.randrange(7, 13)
        max_packet_duration = int(np.ceil(lora_toa(MAX_PL_LORA[sf-7], sf) / self.timeslot))
        startLimit = self.simTimeslots - max_packet_duration

        startSlot = random.randrange(0, startLimit)
        payload_size = random.randrange(13, 58)
        channel = random.randrange(0, 10)

        duration = int(np.ceil(lora_toa(payload_size, sf) / self.timeslot))

        tx = LoRaTransmission(self.nodeId, self.nodeId, startSlot, payload_size, sf, channel, duration)

        return [tx]
    

class LoRaNetwork():

    def __init__(self, simTime, numNodes, numChannels, CR, minEangle, timeGranularity) -> None:
        
        self.CR = CR
        self.numSF = 6
        self.availableSF = [7,8,9,10,11,12]
        self.numNodes = numNodes
        self.numChannels = numChannels

        minPayload = 20

        self.timeGranularity = timeGranularity                    # timeslots per smallest payload
        self.timeslot = lora_toa(minPayload, 7) / timeGranularity # timeslot duration in seconds
        self.simTimeslots = int(np.ceil(simTime / self.timeslot)) # simulation time in slots

        self.nodes = [LoRaNode(i, minEangle, self.simTimeslots, self.timeslot) for i in range(numNodes)]


    def plot_doppler_effect(self, save=False):

        node_x_pos = [node.x/1e3 for node in self.nodes]
        node_y_pos = [node.y/1e3 for node in self.nodes]
        node_shift = [node.doppler_shift/1e3 for node in self.nodes]
        node_rate = [node.doppler_rate for node in self.nodes]

        plt.figure(figsize=(10,8))
        plt.scatter(node_x_pos, node_y_pos, c=node_shift, cmap='bwr', edgecolor='black')
        cbar = plt.colorbar(label='Doppler Shift [kHz]')
        cbar.set_label('Doppler Shift [kHz/s]', fontsize=12)
        cbar.ax.tick_params(labelsize=12)
        plt.xlabel('X Position [km]', fontsize=14)
        plt.ylabel('Y Position [km]', fontsize=14)
        plt.yticks(fontsize=10)
        plt.xticks(fontsize=10)
        plt.title('Doppler shift', fontsize=14)

        if save: plt.savefig(f"dopplershift.pdf")
        else: plt.show()

        plt.figure(figsize=(10,8))
        plt.scatter(node_x_pos, node_y_pos, c=node_rate, cmap='Greens_r', edgecolor='black')
        cbar = plt.colorbar(label='Doppler Rate [Hz/s]')
        cbar.set_label('Doppler Rate [Hz/s]', fontsize=12)
        cbar.ax.tick_params(labelsize=12)
        plt.xlabel('X Position [km]', fontsize=14)
        plt.ylabel('Y Position [km]', fontsize=14)
        plt.yticks(fontsize=10)
        plt.xticks(fontsize=10)
        plt.title('Doppler Rate', fontsize=14)
        
        if save: plt.savefig(f"dopplerrate.pdf")
        else: plt.show()

    def plot_doppler_shift_discrete(self, save=False):
        node_x_pos = [node.x/1e3 for node in self.nodes]
        node_y_pos = [node.y/1e3 for node in self.nodes]
        doppler_shift = [node.doppler_shift for node in self.nodes]  # in Hz

        # Discretize into your specified intervals
        zone_numeric = []
        for d in doppler_shift:
            if d < -10000:
                zone_numeric.append(0)  # High negative
            elif d < -2000:
                zone_numeric.append(1)  # Low negative
            elif d < 2000:
                zone_numeric.append(2)  # Near zero
            elif d < 10000:
                zone_numeric.append(3)  # Low positive
            else:
                zone_numeric.append(4)  # High positive

        # Define boundaries and normalization for 5 discrete zones
        bounds = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5]
        norm = colors.BoundaryNorm(bounds, ncolors=5)

        # Use 'bwr' colormap, which is blue (low), white (middle), red (high)
        cmap = plt.get_cmap('bwr', 5)

        plt.figure(figsize=(10,8))
        scatter = plt.scatter(node_x_pos, node_y_pos, c=zone_numeric, cmap=cmap, norm=norm, edgecolor='black')

        # Custom colorbar
        cbar = plt.colorbar(scatter, ticks=[0, 1, 2, 3, 4])
        cbar.ax.set_yticklabels([
            'High negative (< -10kHz)',
            'Low negative (-10kHz to -2kHz)',
            'Near zero (-2kHz to 2kHz)',
            'Low positive (2kHz to 10kHz)',
            'High positive (> 10kHz)'
        ])
        cbar.set_label('Doppler Shift Zones', fontsize=12)
        cbar.ax.tick_params(labelsize=12)

        plt.xlabel('X Position [km]', fontsize=14)
        plt.ylabel('Y Position [km]', fontsize=14)
        plt.title('Doppler Shift Zones', fontsize=14)

        if save: plt.savefig("doppler_shift_zones.pdf")
        else: plt.show()

    def plot_doppler_rate_discrete(self, save=False):
        node_x_pos = [node.x/1e3 for node in self.nodes]
        node_y_pos = [node.y/1e3 for node in self.nodes]
        doppler_rate = [node.doppler_rate for node in self.nodes]  # in Hz/s

        # Discretize Doppler rate into zones
        zone_numeric = []
        for dr in doppler_rate:
            if dr < -180: zone_numeric.append(0)
            elif dr < -80: zone_numeric.append(1)
            else: zone_numeric.append(2)

        cmap = plt.get_cmap('Greens_r', 3)
        bounds = [-0.5, 0.5, 1.5, 2.5]
        norm = colors.BoundaryNorm(bounds, cmap.N)

        plt.figure(figsize=(10,8))
        scatter = plt.scatter(node_x_pos, node_y_pos, c=zone_numeric, cmap=cmap, norm=norm, edgecolor='black')

        cbar = plt.colorbar(scatter, ticks=[0, 1, 2])
        cbar.ax.set_yticklabels([
            'High doppler rate (< -180 Hz/s)', 
            'Medium doppler rate (-180 to -80 Hz/s)', 
            'Low doppler rate (-80 to 0 Hz/s)'
        ])
        cbar.set_label('Doppler rate zone', fontsize=12)
        cbar.ax.tick_params(labelsize=12)

        plt.xlabel('X Position [km]', fontsize=14)
        plt.ylabel('Y Position [km]', fontsize=14)
        plt.title('Doppler Rate Zones', fontsize=14)

        if save: plt.savefig("doppler_rate_zones.pdf")
        else: plt.show()


    def plot_visibility_time(self, save=False):

        node_x_pos = [node.x/1e3 for node in self.nodes]
        node_y_pos = [node.y/1e3 for node in self.nodes]

        visibility_time = [node.visibility for node in self.nodes]

        plt.figure(figsize=(10,8))
        ax = plt.gca()

        sc = ax.scatter(node_x_pos, node_y_pos, c=visibility_time, cmap='Purples', edgecolor='black')
        cbar = plt.colorbar(sc, label='Visibility time [s]')
        cbar.set_label('Visibility time [s]', fontsize=12)
        cbar.ax.tick_params(labelsize=12)
        plt.xlabel('X Position [km]', fontsize=14)
        plt.ylabel('Y Position [km]', fontsize=14)
        plt.yticks(fontsize=10)
        plt.xticks(fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.title('Visibility time', fontsize=14)

        # Elevation angles and circles
        Eangles = [20, 40, 60, 80]  # degrees
        for E in Eangles:
            radius = ground_distance(np.radians(E)) / 1e3  # Convert to km for plot scale
            circle = plt.Circle((0, 0), radius, fill=False, color='red', linestyle='--', linewidth=2.5, label=f'{E}°')
            ax.add_patch(circle)

        handles = [plt.Line2D([0], [0], color='red', linestyle='--', label=f'{E}°') for E in Eangles]
        ax.legend(handles=handles, title='Elevation Angle')
        ax.set_aspect('equal')

        if save: plt.savefig(f"visibility.pdf")
        else: plt.show()



    def plot_visibility_time_discrete(self, save=False):
        node_x_pos = [node.x/1e3 for node in self.nodes]
        node_y_pos = [node.y/1e3 for node in self.nodes]
        visibility_time = [node.visibility for node in self.nodes]

        # Discretize visibility_time into zones
        zone_numeric = []
        for t in visibility_time:
            if t <= 200: zone_numeric.append(0)
            elif t <= 600: zone_numeric.append(1)
            else: zone_numeric.append(2)

        # Use 3 discrete colors from 'Purples'
        cmap = plt.get_cmap('Purples', 3)
        bounds = [-0.5, 0.5, 1.5, 2.5]
        norm = colors.BoundaryNorm(bounds, cmap.N)

        plt.figure(figsize=(10,8))
        scatter = plt.scatter(node_x_pos, node_y_pos, c=zone_numeric, cmap=cmap, norm=norm, edgecolor='black')

        # Custom colorbar
        cbar = plt.colorbar(scatter, ticks=[0, 1, 2])
        cbar.ax.set_yticklabels(['Low (0-200s)', 'Medium (200-600s)', 'High (>600s)'])
        cbar.set_label('Visibility time zones', fontsize=12)
        cbar.ax.tick_params(labelsize=12)

        plt.xlabel('X Position [km]', fontsize=14)
        plt.ylabel('Y Position [km]', fontsize=14)
        plt.yticks(fontsize=10)
        plt.xticks(fontsize=10)
        plt.title('Visibility time zones', fontsize=14)
        plt.grid(True, alpha=0.3)

        if save: plt.savefig("visibility.pdf")
        else: plt.show()


    def plot_ground_constraints(self, save=False):

        node_x_pos = [node.x/1e3 for node in self.nodes]
        node_y_pos = [node.y/1e3 for node in self.nodes]
        node_shift = [node.doppler_shift/1e3 for node in self.nodes]
        node_rate = [node.doppler_rate for node in self.nodes]
        node_dist = [np.sqrt(node.ground_dist**2 + SAT_H**2) for node in self.nodes]

        for sf in self.availableSF:
            ldro = 1 if sf >= 11 else 0

            success=0
            plt.figure(figsize=(10,10))
            for i in range(self.numNodes):

                P_r = received_power(node_dist[i])
                if doppler_shift_success(node_shift[i], sf) and linkbudget_success(P_r, sf):
                    success+=1
                    plt.scatter(node_x_pos[i], node_y_pos[i], marker='o', color='blue')
                else:
                    plt.scatter(node_x_pos[i], node_y_pos[i], marker='x', color='red')

            print(f"sf={sf}, success = {(success/self.numNodes):.2f}; fail = {((self.numNodes-success)/self.numNodes):.2f}")

            plt.xlabel('X Position [km]')
            plt.ylabel('Y Position [km]')
            plt.title(f'Doppler Effect and Link Budget constraints, PL={PL_BYTES}, SF={sf}, LDRO={ldro}, success={(success/self.numNodes):.2f}')
            if save: plt.savefig(f"img/TEST_BW125_lora_sf{sf}.jpg")
            else: plt.show()


    def plot_sf_linkbudget(self, save=False):
        colors_ = ['#FF0000','#00FF00','#0000FF','#FF00FF','#00FFFF','#FFA500']
        
        node_x_pos = [node.x/1e3 for node in self.nodes]
        node_y_pos = [node.y/1e3 for node in self.nodes]
        node_dist = [np.sqrt(node.ground_dist**2 + SAT_H**2) for node in self.nodes]

        plt.figure(figsize=(10,10))
        ax = plt.gca()

        # For each node, find the LOWEST valid SF
        sf_legend_added = set()  # Track which SFs have been added to legend
        for i in range(self.numNodes):
            # Check SFs in ascending order to find the first (lowest) valid one
            for sf in sorted(self.availableSF):
                P_r = received_power(node_dist[i])
                if linkbudget_success(P_r, sf):
                    # Only add label for SF if it's the first occurrence
                    label = f'SF{sf}' if sf not in sf_legend_added else ""
                    sc = ax.scatter(node_x_pos[i], node_y_pos[i], color=colors_[sf-7], label=label)
                    if label: sf_legend_added.add(sf)
                    break

        # Elevation angles and circles
        Eangles = [20, 40, 60, 80]  # degrees
        elevation_handles = []
        for E in Eangles:
            radius = ground_distance(np.radians(E)) / 1e3  # Convert to km
            circle = plt.Circle((0, 0), radius, fill=False, color='black', 
                                linestyle='--', linewidth=2.5)
            ax.add_patch(circle)
            # Create proxy artist for legend
            elevation_handles.append(plt.Line2D([0], [0], color='black', linestyle='--', 
                                                label=f'{E}°', linewidth=2.5))

        # Combine SF and elevation legends
        sf_handles, sf_labels = ax.get_legend_handles_labels()
        all_handles = sf_handles + elevation_handles
        all_labels = [h.get_label() for h in all_handles]

        plt.legend(all_handles, all_labels, loc='upper right', fontsize=10,
                title='SF / Elevation Angle', title_fontsize=11)

        plt.xlabel('X Position [km]', fontsize=14)
        plt.ylabel('Y Position [km]', fontsize=14)
        plt.title('SF Link Budget Constraints', fontsize=14)
        plt.yticks(fontsize=10)
        plt.xticks(fontsize=10)
        ax.set_aspect('equal')
        plt.grid(True, alpha=0.3)

        
        if save: plt.savefig("img/TEST_BW125_lora_sf.jpg")  # Removed {sf} from filename
        else: plt.show()


    def set_transmissions(self) -> list[LoRaTransmission]:

        transmissions = []
        node : LoRaNode
        for node in self.nodes:
            transmissions += node.get_transmissions()

        sorted_txs = sorted(transmissions)
        #for tx in sorted_txs: print(tx)

        return sorted_txs
    

    ####################################
    # TIME-FREQ(CH) MATRIX GENERATOR METHODS
    ####################################

    def get_rcvM(self, transmissions: list[LoRaTransmission], power: bool) -> np.ndarray:
        """
        Create received matrix from given transmissions sets.
        The power flag on will output a matrix based on received power.
        When the power flag is off, the output matrix is based on counts.
        """

        # count based received matrix
        RXpower = 1
        rcvM = np.zeros((self.numSF, self.numChannels, self.simTimeslots))

        # power based received matrix
        if power: 
            rcvM = np.random.rayleigh(1, (self.numSF, self.numChannels, self.simTimeslots))
            rcvM = (rcvM / np.linalg.norm(rcvM)) * np.sqrt(dBm2mW(AWGN_VAR_DB))

        # add transmissions to received matrix
        tx : LoRaTransmission
        for tx in transmissions:

            time = tx.startSlot

            endTime = time + tx.duration
            rcvM[int(tx.sf-7), tx.channel, time : endTime] += (np.ones((tx.duration)) * RXpower)
            time = endTime

        return rcvM
    
