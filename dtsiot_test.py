from src.base import *
from src.network.DtSIoTNetwork import DtSIoTNetwork

np.random.seed(42)

points = [
    (48.16506850944985, -3.5833598413239546),
    (48.667165569993934, 4.977622353048859),
    (46.907793438371776, 1.38067874956546355),
    (42.79516320966049, 2.3097125314976026),
    (50.716059725651, 2.2728539240359815)
]

ts = load.timescale()
t0 = ts.utc(2025,6,2)
t1 = ts.utc(2025,6,3)
delta = 20

altitude_degrees = 0.0
lat, lon = points[0]
point = wgs84.latlon(lat, lon)

#plot_elevationangles(points, t0, t1, delta, altitude_degrees)

#plot_elevationangles_constellation(KINEIS_CONSTELLATION, point, t0, t1, delta)

#plot_dopplereffect(lat, lon, t0, t1, delta, altitude_degrees)

#plot_enddevices(points)

#plot_best_satellite_passes(points, t0, t1)

#plot_sat_track(points, t0, t1, delta)

#plot_alllaps_SFcurve(points, t0, t1)

#plot_sat_altitude(t0, t1, delta)

#get_bestSF_coverage_time(lat, lon, t0, t1)

#plot_toa()

#print_toa()

#max_tx_count()

#plot_lora_linkbudget()

#write_locations(3000, "locations3k.txt")

#plot_best_SFcurve(points, t0, t1, COLORS1)

#print(round(max_sf12_range()/1e3))


t0 = ts.utc(2025,6,2,7,15)
t1 = ts.utc(2025,6,2,7,22)
numDevices = 100
slottime = 1 # lora_toa(PL_BYTES, 11)
locationsfilename = "locations.txt"
datafile = ""
timeslots = int(np.ceil(round(float(t1 - t0) * 86400) / slottime))
save_sache = False

network = DtSIoTNetwork(numDevices, t0, slottime, timeslots, 1,
                        1, locationsfilename, datafile, save_sache)

network.plot_bestSF_map()
#network.plot_heatmapSF()
#network.plot_bestSF_ocurrences()
#network.plot_availableSF_map(11)
