from src.base import *
from src.network.DtSIoTNetwork import DtSIoTNetwork
np.random.seed(42)

ts = load.timescale()
t0 = ts.utc(2025,10,20,16,14)  # kineis (2025,10,24,17,45) - starlink (2025,10,20,16,14)
t1 = ts.utc(2025,10,20,16,30)  # kineis (2025,10,24,17,54) - starlink (2025,10,20,16,30)

#constellation = ['KINEIS-1D', 'KINEIS-1E']
constellation = STARLINK_CONSTELLATION2

slottime = lora_toa(PL_BYTES, 10)
timeslots = int(np.ceil(round(float(t1 - t0) * 86400) / slottime))
numLRchannels = 1
numFHSSchannles = 1
numDevices = 300
locationsfilename = "locations.txt"
datafile = "6sats_300EDs_2912slots.json" # "6sats_300EDs_2912slots.json" # "2sats_300EDs_182slots.json"
save_sache = False

network = DtSIoTNetwork(constellation, numDevices, t0, slottime, timeslots, numLRchannels,
                        numFHSSchannles, locationsfilename, datafile, save_sache)

runs = 40
uplink_period = 60 # seconds
sizes = np.linspace(10,300,10,dtype=int)
numEDs = 300

#network.plot_bestSF_map()
#network.plot_heatmapSF()
#network.plot_heatmapSF_ULperiods(uplink_period)

#print(sizes)
#network.schedule_single_window(sizes, runs, config=1)
network.schedule_multiple_window(numEDs, uplink_period, runs, config=1)
