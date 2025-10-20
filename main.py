from src.base import *
from src.network.DtSIoTNetwork import DtSIoTNetwork
np.random.seed(42)

ts = load.timescale()
t0 = ts.utc(2025,6,2,16,25)  # 15 (2025,6,2,7,18) 
t1 = ts.utc(2025,6,2,16,50)  # 22 (2025,6,2,7,18)

satname = 'KINEIS-5A'

slottime = 1# lora_toa(PL_BYTES, 10)
timeslots = int(np.ceil(round(float(t1 - t0) * 86400) / slottime))
numLRchannels = 1
numFHSSchannles = 1
numDevices = 20
locationsfilename = "locations.txt"
datafile = "" # data_200EDs_546slots.json data_300EDs_1274slots.json
save_sache = False

network = DtSIoTNetwork(satname, numDevices, t0, slottime, timeslots, numLRchannels,
                        numFHSSchannles, locationsfilename, datafile, save_sache)

runs = 40
uplink_period = 60 # seconds
sizes = np.linspace(10,3000,20,dtype=int)
numEDs = 20

#network.plot_bestSF_map()
network.plot_heatmapSF()
#network.plot_heatmapSF_ULperiods(uplink_period)

#print(sizes)
#network.schedule_single_window(sizes, runs, config=1)
#network.schedule_multiple_window(numEDs, uplink_period, runs, config=1)
