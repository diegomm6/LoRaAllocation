from base import *
from LoRaNetwork import LoRaNetwork


if __name__ == "__main__":
    random.seed(1234)

    numNodes = 5000
    simTime = 5
    numChannels = 10
    CR=1
    minEangle = 0 * np.pi /180
    timeGranularity = 5

    network = LoRaNetwork(simTime, numNodes, numChannels, CR, minEangle, timeGranularity)

    transmissions = network.set_transmissions()
    rcvM = network.get_rcvM(transmissions, False)

    collided = np.copy(rcvM)
    collided[collided > 2] = 2

    def plot_sf_channels(sf):
        fig = plt.figure(figsize=(18,12))
        im = plt.imshow(collided[sf-7], extent =[0, simTime, 0, numChannels], interpolation ='none', aspect='auto')
        fig.colorbar(im)
        plt.title(f'received lora sf={sf}, {numChannels} channels, {numNodes} total txs', fontsize=18)
        plt.xlabel('seconds', fontsize=18)
        plt.ylabel('channel', fontsize=18)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        plt.show()
        #plt.savefig(save)
        plt.close('all')

    for sf in [7,8,9,10,11,12]:
        break
        plot_sf_channels(sf)

    network.plot_ground_constraints()
    #network.plot_doppler_effect(True)
    

