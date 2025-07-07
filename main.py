from src.base import *
from src.network.DtSIoTNetwork import DtSIoTNetwork
np.random.seed(42)

ts = load.timescale()
t0 = ts.utc(2025,6,2,7,15)  # 15  16
t1 = ts.utc(2025,6,2,7,22)  # 22  19

slottime = lora_toa(PL_BYTES, 10)
timeslots = int(np.ceil(round(float(t1 - t0) * 86400) / slottime))
numLRchannels = 1
numFHSSchannles = 1
numDevices = 300
locationsfilename = "locations.txt"
datafile = "data_300EDs_1274slots.json" # data_200EDs_546slots.json data_300EDs_1274slots.json
save_sache = False

network = DtSIoTNetwork(numDevices, t0, slottime, timeslots, numLRchannels,
                        numFHSSchannles, locationsfilename, datafile, save_sache)

runs = 40
uplink_period = 60 # seconds
sizes = np.linspace(10,200,30,dtype=int)
numEDs = 200

#network.plot_bestSF_map()
#network.plot_heatmapSF()
#network.plot_heatmapSF_ULperiods(uplink_period)

#network.schedule_single_window(sizes, runs, config=2)
network.schedule_multiple_window(numEDs, uplink_period, runs, config=1)
