from src.base import *
from src.network.DtSIoTNetwork import DtSIoTNetwork
np.random.seed(42)

ts = load.timescale()
t0 = ts.utc(2025,10,20,16,23,00)  # kineis (2025,10,24,17,45) - starlink (2025,10,20,16,15) - single window 16,23,00
t1 = ts.utc(2025,10,20,16,23,15)  # kineis (2025,10,24,17,54) - starlink (2025,10,20,16,30) - single window 16,23,15

#constellation = ['KINEIS-1D'] # , 'KINEIS-1E'
constellation = STARLINK_CONSTELLATION2

slottime = lora_toa(PL_BYTES, 9)
timeslots = int(np.ceil(round(float(t1 - t0) * 86400) / slottime))
numLRchannels = 3
numFHSSchannles = 1
numDevices = 300
locationsfilename = "locations.txt"
datafile = "6sats_1000EDs_91slots.json" # "6sats_300EDs_5460slots.json" # "6sats_1000EDs_91slots.json" # 1sats_300EDs_1274slots.json
save_sache = False

network = DtSIoTNetwork(constellation, numDevices, t0, slottime, timeslots, numLRchannels,
                        numFHSSchannles, locationsfilename, datafile, save_sache)

runs = 40
uplink_period = 60 # seconds
sizes = np.linspace(5,100,5,dtype=int)
numEDs = 300

#network.plot_bestSF_map()
#network.plot_heatmapSF()
#network.plot_heatmapSF_ULperiods(uplink_period, True, 100)

network.schedule_single_window(sizes, runs, config=3)
#network.schedule_multiple_window(numEDs, uplink_period, runs, config=2)
