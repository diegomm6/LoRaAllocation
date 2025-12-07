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
        self.maxGround_dist = EARTH_R * np.arcsin( maxRange*np.cos(minEangle) / (EARTH_R+SAT_H) )

        self.nodeId = id_
        self.ground_dist = self.maxGround_dist * np.sqrt(random.uniform(0, 1))
        self.b_angle = random.uniform(0, 2*np.pi)

        self.x = self.ground_dist * np.cos(self.b_angle)
        self.y = self.ground_dist * np.sin(self.b_angle)
        self.dist2sat = np.sqrt(self.ground_dist**2 + SAT_H**2)

        self.TXtime = -self.y / SAT_V
        self.maxE_angle = np.arctan( SAT_H / abs(self.x) )

        doppler_data = doppler(self.maxE_angle, self.TXtime)
        self.doppler_shift = doppler_data[0]  
        self.doppler_rate = doppler_data[1]

        self.visibility = (self.y + np.sqrt(self.maxGround_dist**2 - self.x**2)) / SAT_V


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

        if save: plt.savefig(f"img/dopplershift.pdf")
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
        
        if save: plt.savefig(f"img/dopplerrate.pdf")
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
        
        node_dist = [node.dist2sat for node in self.nodes]
        sorted_nodes = [node for _, node in sorted(zip(node_dist, self.nodes), key=lambda x: x[0])]

        plt.figure(figsize=(8,8))
        ax = plt.gca()

        # For each node, find the LOWEST valid SF
        sf_legend_added = set()  # Track which SFs have been added to legend
        for node in sorted_nodes:
            # Check SFs in ascending order to find the first (lowest) valid one
            for sf in sorted(self.availableSF):
                P_r = received_power(node.dist2sat)
                if linkbudget_success(P_r, sf):
                    # Only add label for SF if it's the first occurrence
                    label = f'SF{sf}' if sf not in sf_legend_added else ""
                    sc = ax.scatter(node.x/1e3, node.y/1e3, color=colors_[sf-7], label=label)
                    if label: sf_legend_added.add(sf)
                    break

        # Elevation angles and circles
        #Eangles = [20, 40, 60, 80]  # degrees
        Eangles = [elevation_flat(sf) for sf in [2,3,4,5]]
        linestyles = ['-', '--', '-.', ':']
        elevation_handles = []
        for i, E in enumerate(Eangles):
            radius = ground_distance(np.radians(E)) / 1e3  # Convert to km
            circle = plt.Circle((0, 0), radius, fill=False, color='black', linestyle=linestyles[i], linewidth=2.5)
            ax.add_patch(circle)
            elevation_handles.append(plt.Line2D([0], [0], color='black', linestyle=linestyles[i], label=f'{round(E,1)}°', linewidth=2.5))

        # Combine SF and elevation legends
        sf_handles, sf_labels = ax.get_legend_handles_labels()
        all_handles = sf_handles + elevation_handles
        all_labels = [h.get_label() for h in all_handles]

        plt.legend(all_handles, all_labels, loc='upper right', fontsize=10, title='SF / Elevation Angle', title_fontsize=11)
        plt.xlabel('X Position [km]', fontsize=14)
        plt.ylabel('Y Position [km]', fontsize=14)
        plt.title('SF Link Budget Constraints', fontsize=14)
        plt.yticks(fontsize=10)
        plt.xticks(fontsize=10)
        ax.set_aspect('equal')
        plt.grid(True, alpha=0.3)

        
        if save: plt.savefig("img/lora_sf_budget.pdf")  # Removed {sf} from filename
        else: plt.show()


    def plot_cr_allocation(self, save=False):
        colors_ = ['#FF0000','#00FF00']
        
        node_dist = [node.dist2sat for node in self.nodes]
        sorted_nodes = [node for _, node in sorted(zip(node_dist, self.nodes), key=lambda x: x[0])]

        plt.figure(figsize=(8,8))
        ax = plt.gca()

        # For each node, find the LOWEST valid SF
        sf_legend_added = set()  # Track which SFs have been added to legend
        for node in sorted_nodes:
            # Check SFs in ascending order to find the first (lowest) valid one
            for sf in [0,1]:
                P_r = received_power(node.dist2sat)
                elevation = angle_dist2sat(node.dist2sat) * 180/np.pi
                if elevation < 32.6:
                    # Only add label for SF if it's the first occurrence
                    label = f'CR1/3' if sf not in sf_legend_added else ""
                    sc = ax.scatter(node.x/1e3, node.y/1e3, color=colors_[0], label=label)
                    if label: sf_legend_added.add(sf)
                    break
                else:
                    # Only add label for SF if it's the first occurrence
                    label = f'CR2/3' if sf not in sf_legend_added else ""
                    sc = ax.scatter(node.x/1e3, node.y/1e3, color=colors_[1], label=label)
                    if label: sf_legend_added.add(sf)
                    break

        # Elevation angles and circles
        #Eangles = [20, 40, 60, 80]  # degrees
        #Eangles = [elevation_flat(sf) for sf in [2,3,4,5]]
        Eangles = [18, 32.6]
        linestyles = ['-', '--', '-.', ':']
        elevation_handles = []
        for i, E in enumerate(Eangles):
            radius = ground_distance(np.radians(E)) / 1e3  # Convert to km
            circle = plt.Circle((0, 0), radius, fill=False, color='black', linestyle=linestyles[i], linewidth=2.5)
            ax.add_patch(circle)
            elevation_handles.append(plt.Line2D([0], [0], color='black', linestyle=linestyles[i], label=f'{E}°', linewidth=2.5))

        # Combine SF and elevation legends
        sf_handles, sf_labels = ax.get_legend_handles_labels()
        all_handles = sf_handles + elevation_handles
        all_labels = [h.get_label() for h in all_handles]

        plt.legend(all_handles, all_labels, loc='upper right', fontsize=10, title='SF / Elevation Angle', title_fontsize=11)
        plt.xlabel('X Position [km]', fontsize=14)
        plt.ylabel('Y Position [km]', fontsize=14)
        plt.title('CR allocation', fontsize=14)
        plt.yticks(fontsize=10)
        plt.xticks(fontsize=10)
        ax.set_aspect('equal')
        plt.grid(True, alpha=0.3)

        
        if save: plt.savefig("img/lrfhss_cr_allocation.pdf")  # Removed {sf} from filename
        else: plt.show()


    def get_shift_time_angle(self, runs=100):

        node_x_pos = [node.x/1e3 for node in self.nodes]
        node_y_pos = [node.y/1e3 for node in self.nodes]

        deployment_radius = self.nodes[0].maxGround_dist

        r = deployment_radius * np.sqrt(random.uniform(0, 1))
        theta = random.uniform(0, 2 * np.pi)
        a = r * np.cos(theta)
        b = r * np.sin(theta)

        a,b=0,0

        # Step 2: Select nodes within sample circle
        L = 500e3  # 500 km
        sample_nodes = [
            node for node in self.nodes
            if np.sqrt((node.x - a) ** 2 + (node.y - b) ** 2) <= L
        ]

        all_shift_diff = []
        all_time_diff = []
        all_angle_diff = []

        shift = [node.doppler_shift/1e3 for node in sample_nodes]
        maxEangle = [node.maxE_angle*180/np.pi for node in sample_nodes]
        visibility_time = [node.visibility for node in sample_nodes]

        print(f"angle diff {round(max(maxEangle) - min(maxEangle))}")
    
        plt.figure(figsize=(8, 6))
        plt.scatter(maxEangle, visibility_time, c=shift, cmap='bwr', edgecolor='black')
        cbar = plt.colorbar(label='Doppler Shift [kHz]')
        cbar.set_label('Doppler Shift [kHz/s]', fontsize=12)
        cbar.ax.tick_params(labelsize=12)
        plt.xlabel('maxEangle (o)')
        plt.ylabel('visibility time (s)')
        plt.title('visibility time vs maxEangle ')
        plt.grid(True)
        #plt.show()

        #a_pos = np.linspace(-deployment_radius, deployment_radius, 10000)
        
        #for a in a_pos:
        for w in range(runs):
            random.seed(33*w)
            r = deployment_radius * np.sqrt(random.uniform(0, 1))
            theta = random.uniform(0, 2 * np.pi)
            a = r * np.cos(theta)
            b = r * np.sin(theta)

            # Step 2: Select nodes within sample circle
            L = 500e3  # 500 km
            sample_nodes = [
                node for node in self.nodes
                if np.sqrt((node.x - a) ** 2 + (node.y - b) ** 2) <= L
            ]

            shift = [node.doppler_shift/1e3 for node in sample_nodes]
            maxEangle = [node.maxE_angle*180/np.pi for node in sample_nodes]
            visibility_time = [node.visibility for node in sample_nodes]

            all_shift_diff.append(max(shift) - min(shift))
            all_time_diff.append(max(visibility_time) - min(visibility_time))
            all_angle_diff.append(max(maxEangle) - min(maxEangle))

            sample_x_pos = [node.x/1e3 for node in sample_nodes]
            sample_y_pos = [node.y/1e3 for node in sample_nodes]

            if 1:
                fig, ax = plt.subplots(figsize=(10, 9))
                sc = ax.scatter(node_x_pos, node_y_pos, color='blue', label='Deployed Nodes')
                ax.scatter(sample_x_pos, sample_y_pos, color='red', label='Selected Nodes')

                radius = ground_distance(np.radians(20)) / 1e3  # Convert to km for plot scale
                #circle = plt.Circle((0, 0), radius, fill=False, color='pink', linestyle='-', linewidth=2.5, label=f'{20}°')
                #ax.add_patch(circle)

                circle = plt.Circle((a/1e3, b/1e3), L/1e3, fill=False, color='black', linestyle='--', linewidth=2.5)
                ax.add_patch(circle)

                # Axis labels and title
                ax.set_xlabel('X Position [km]', fontsize=14)
                ax.set_ylabel('Y Position [km]', fontsize=14)
                ax.tick_params(axis='both', labelsize=10)
                ax.set_title('Deplyment region from satellite perspective', fontsize=14)
                #ax.legend()
                plt.show()

                plt.figure(figsize=(8, 6))
                plt.scatter(maxEangle, visibility_time, c=shift, cmap='bwr', edgecolor='black')
                cbar = plt.colorbar(label='Doppler Shift [kHz]')
                cbar.set_label('Doppler Shift [kHz/s]', fontsize=12)
                cbar.ax.tick_params(labelsize=12)
                plt.xlabel('maxEangle (o)')
                plt.ylabel('visibility time (s)')
                plt.title('visibility time vs maxEangle ')
                plt.grid(True)
                plt.show()


        return
        # report meand and std for differences
        print(f"Mean shift difference: {np.mean(all_shift_diff):.2f} Hz, Std: {np.std(all_shift_diff):.2f} Hz")
        print(f"Mean visibility time difference: {np.mean(all_time_diff):.2f} s, Std: {np.std(all_time_diff):.2f} s")
        print(f"Mean maxEangle difference: {np.mean(all_angle_diff):.2f} degrees, Std: {np.std(all_angle_diff):.2f} degrees")

        # report min and max difference
        print(f"Min shift difference: {min(all_shift_diff):.2f} Hz, Max shift difference: {max(all_shift_diff):.2f} Hz")
        print(f"Min visibility time difference: {min(all_time_diff):.2f} s, Max visibility time difference: {max(all_time_diff):.2f} s")
        print(f"Min maxEangle difference: {min(all_angle_diff):.2f} degrees, Max maxEangle difference: {max(all_angle_diff):.2f} degrees")



        plt.plot([abs(a/1e3) for a in a_pos], all_angle_diff)
        plt.xlabel('Distance from center (km)')
        plt.ylabel('Max Angle Difference (degrees)')
        plt.title('Max Angle Difference vs Distance from Center')
        plt.grid(True)
        plt.show()


        return 


        x = [[s, e, v] for s, e, v in zip(shift, maxEangle, visibility_time)]

        def vector_to_time_slot(x, t_start, t_end, n_slots):
            vector_bytes = str(x).encode('utf-8')
            hash_digest = hashlib.sha256(vector_bytes).digest()
            hash_int = int.from_bytes(hash_digest, 'big')
            max_hash = 2 ** (8 * len(hash_digest)) - 1
            norm = hash_int / max_hash
            slot = int(norm * n_slots)
            # Ensure slot is within [0, n_slots-1]
            if slot == n_slots:
                slot = n_slots - 1
            # Map slot to time (centered in the slot)
            slot_duration = (t_end - t_start) / n_slots
            t = t_start + slot * slot_duration + slot_duration / 2
            return slot
        
        t_start = 0
        t_end = 99
        n_slots = 100
        tx_times = [vector_to_time_slot(xi, t_start, t_end, n_slots) for xi in x] 


        print(f"min shift: {round(min(shift))} Hz, max shift: {round(max(shift))} Hz")
        print(f"min maxEangle: {round(min(maxEangle))} angles, max maxEangle: {round(max(maxEangle))} angles")
        print(f"min visibility time: {round(min(visibility_time))} s, max visibility time: {round(max(visibility_time))} s")

        if 0:
            fig, ax = plt.subplots(figsize=(10, 9))
            sc = ax.scatter(node_x_pos, node_y_pos, color='blue', label='Deployed Nodes')
            ax.scatter(sample_x_pos, sample_y_pos, color='red', label='Selected Nodes')

            circle = plt.Circle((a/1e3, b/1e3), L/1e3, fill=False, color='black', linestyle='--', linewidth=2.5)
            ax.add_patch(circle)

            # Axis labels and title
            ax.set_xlabel('X Position [km]', fontsize=14)
            ax.set_ylabel('Y Position [km]', fontsize=14)
            ax.tick_params(axis='both', labelsize=10)
            ax.set_title('Node Deployment and Selected Sample Region', fontsize=14)
            ax.legend()
            plt.show()

        plt.figure(figsize=(8, 5))
        plt.hist(tx_times, bins=n_slots, range=(0, n_slots), align='left', rwidth=0.8, color='skyblue', edgecolor='black')
        plt.xlabel('Time Slot Index')
        plt.ylabel('Number of Nodes')
        plt.title('Histogram of Nodes per Time Slot with hash function')
        plt.xticks(range(n_slots))
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show()

        tx_times_random = [random.randint(0, n_slots - 1) for _ in range(len(x))]

        plt.figure(figsize=(8, 5))
        plt.hist(tx_times_random, bins=n_slots, range=(0, n_slots), align='left', rwidth=0.8, color='skyblue', edgecolor='black')
        plt.xlabel('Time Slot Index')
        plt.ylabel('Number of Nodes')
        plt.title('Histogram of Nodes per Time Slot with Random Uniform')
        plt.xticks(range(n_slots))
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show()

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
    
