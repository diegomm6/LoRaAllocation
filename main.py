from src.base import *
from src.network.DtSIoTNetwork import DtSIoTNetwork
np.random.seed(42)

ts = load.timescale()
t0 = ts.utc(2025,6,2,7,15)
t1 = ts.utc(2025,6,2,7,22)

slottime = lora_toa(PL_BYTES, 11)
timeslots = int(np.ceil(round(float(t1 - t0) * 86400) / slottime))
numLRchannels = 1
numFHSSchannles = 1
numDevices = 1000
locationsfilename = "locations.txt"
datafile = ""
save_sache = False

network = DtSIoTNetwork(numDevices, t0, slottime, timeslots, numLRchannels,
                        numFHSSchannles, locationsfilename, datafile, save_sache)

if 0:
    uplink_period = 60
    beacon_time = int(timeslots / 6)
    network.plot_heatmapSF_ULperiods(uplink_period, True, 50)
    network.solve_scheduling("1D")
    network.solve_scheduling("2D")
    network.solve_scheduling("distributed")
    network.solve_scheduling("lrfhss")


sizes = np.linspace(1,500,10,dtype=int)
#network.run_simulation(sizes, "1D")

#network.solve_scheduling_per_beacon(300, beacon_time)
#network.solve_distributed_scheduling(200, beacon_time)

#network.compare_methods(sizes)
#network.plot_bestSF_map()
#network.plot_heatmapSF()
#network.plot_bestSF_ocurrences()

