import numpy as np
from base import *
from LoRaTransmission import LoRaTransmission
from LoRaNode import LoRaNode


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

                P_r_MON_RF_FE = received_power(P_t_RF_FE, G_t_MON, G_r_MON, node_dist[i], CHANNEL_FC, L_point_MON)

                if doppler_success(node_shift[i], node_rate[i], sf) and linkbudget_success(P_r_MON_RF_FE, sf):
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

            # power based received matrix
            #if power:
                #RXpower = fspl_w(tx.distance)

            endTime = time + tx.duration
            rcvM[int(tx.sf-7), tx.channel, time : endTime] += (np.ones((tx.duration)) * RXpower)
            time = endTime

        return rcvM
    


