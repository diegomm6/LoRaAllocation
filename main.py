from src.base import *
from src.network.DtSIoTNetwork import DtSIoTNetwork
np.random.seed(42)

ts = load.timescale()
t0 = ts.utc(2025,6,2,7,16)  # 15  16
t1 = ts.utc(2025,6,2,7,19)  # 22  19

slottime = lora_toa(PL_BYTES, 10)
timeslots = int(np.ceil(round(float(t1 - t0) * 86400) / slottime))
numLRchannels = 1
numFHSSchannles = 1
numDevices = 200
locationsfilename = "locations.txt"
datafile = "data_200EDs_546slots.json" # data_200EDs_546slots.json
save_sache = False

network = DtSIoTNetwork(numDevices, t0, slottime, timeslots, numLRchannels,
                        numFHSSchannles, locationsfilename, datafile, save_sache)

#network.plot_bestSF_map()
#network.plot_heatmapSF()

uplink_period = 30 # seconds
#network.plot_heatmapSF_ULperiods(uplink_period)
network.schedule_multiple_window(20, uplink_period, 4)

sizes = np.linspace(10,200,20,dtype=int)
#network.schedule_single_window(sizes, 40)
