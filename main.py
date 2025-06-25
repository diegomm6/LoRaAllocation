from src.base import *
from src.network.DtSIoTNetwork import DtSIoTNetwork
np.random.seed(42)

ts = load.timescale()
t0 = ts.utc(2025,6,2,7,15)  # 15
t1 = ts.utc(2025,6,2,7,22)  # 22

slottime = lora_toa(PL_BYTES, 10)
timeslots = int(np.ceil(round(float(t1 - t0) * 86400) / slottime))
numLRchannels = 1
numFHSSchannles = 1
numDevices = 100
locationsfilename = "locations.txt"
datafile = "data_100EDs_1274slots.json" # data_500EDs_91slots.json
save_sache = False

network = DtSIoTNetwork(numDevices, t0, slottime, timeslots, numLRchannels,
                        numFHSSchannles, locationsfilename, datafile, save_sache)

if 1:
    uplink_period = 60
    beacon_time = int(timeslots / 7)
    network.plot_heatmapSF_ULperiods(uplink_period)


sizes = np.linspace(10,50,3,dtype=int)

#network.run_simulation(sizes)
network.solve_scheduling_per_beacon(100, beacon_time, 20)

#network.compare_methods(sizes)
#network.plot_bestSF_map()
#network.plot_heatmapSF()
#network.plot_bestSF_ocurrences()

#network.compare_joint_methods(sizes, 30)
#print(LoRA_success_prob(11, 100))

