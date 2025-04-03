from base import *
from DtSIoTNetwork import DtSIoTNetwork

np.random.seed(42)

points = [
    (48.16506850944985, -3.5833598413239546),
    (48.667165569993934, 4.977622353048859),
    (46.907793438371776, 1.38067874956546355),
    (42.79516320966049, 2.3097125314976026),
    (50.716059725651, 2.2728539240359815)
]

kineis_constellation = ['KINEIS-1A', 'KINEIS-1B', 'KINEIS-1C', 'KINEIS-1D', 'KINEIS-1E',
                        'KINEIS-3A', 'KINEIS-3B', 'KINEIS-3C', 'KINEIS-3D', 'KINEIS-3E',
                        'KINEIS-5A', 'KINEIS-5B', 'KINEIS-5C', 'KINEIS-5D', 'KINEIS-5E']

default_colors = [u'#1f77b4', u'#ff7f0e', u'#2ca02c', u'#d62728', u'#9467bd',
                  u'#8c564b', u'#e377c2', u'#7f7f7f', u'#bcbd22', u'#17becf']

colors_ = [
    '#FF0000',    # Red
    '#00FF00',    # Lime
    '#0000FF',    # Blue
    '#FF00FF',    # Magenta
    '#00FFFF',    # Cyan
    '#FFA500',    # Orange
    '#800080',    # Purple
    '#008000',    # Green
    '#FFD700',    # Gold
    '#FF69B4',    # Hot Pink
    '#4B0082',    # Indigo
    '#A0522D',    # Sienna
    '#00CED1',    # Dark Turquoise
    '#FF4500',    # Orange Red
    '#2F4F4F'     # Dark Slate Gray
]

ts = load.timescale()
t0 = ts.utc(2024,12,1)
t1 = ts.utc(2024,12,2)

altitude_degrees = 0.0
lat, lon = points[0]
point = wgs84.latlon(lat, lon)

#plot_elevationangles(points, t0, t1, altitude_degrees, default_colors)

#plot_elevationangles_constellation(kineis_constellation, point, t0, t1, colors_)

#plot_dopplereffect(lat, lon, t0, t1, altitude_degrees)

#plot_enddevices(points)

#plot_best_satellite_passes(points, t0, t1)

#plot_sat_track(points, t0, t1)

#plot_alllaps_SFcurve(points, t0, t1)

#plot_sat_altitude(t0, t1)

#get_bestSF_coverage_time(lat, lon, t0, t1)

#plot_toa()

#print_toa()

#max_tx_count()

#plot_lora_linkbudget()

#write_locations(3000, "locations3k.txt")

#plot_best_SFcurve(points, t0, t1, default_colors)

#print(round(max_sf12_range()/1e3))


t0 = ts.utc(2024,12,1,7,30,48)
t1 = ts.utc(2024,12,1,7,32,48)
numDevices = 20
slottime = 1 # lora_toa(PL_BYTES, 11)
timeslots = int(np.ceil(round(float(t1 - t0) * 86400) / slottime))

#network = DtSIoTNetwork(numDevices, t0, slottime, timeslots, 1, 1)
#network.plot_bestSF_map()
#network.plot_heatmapSF()
#network.plot_bestSF_ocurrences()
#network.plot_availableSF_map(11)


t0 = ts.utc(2024,12,1,7,28,48) # 7,28,48
t1 = ts.utc(2024,12,1,7,34,48) # 7,34,48

slottime = lora_toa(PL_BYTES, 11)
timeslots = int(np.ceil(round(float(t1 - t0) * 86400) / slottime))
numLRchannels = 3
numFHSSchannles = 1
numDevices = 3000
locationsfilename = "locations3k.txt"
datafile = "data_3000EDs_546slots.json"
save_sache = False

network = DtSIoTNetwork(numDevices, t0, slottime, timeslots, numLRchannels,
                        numFHSSchannles, locationsfilename, datafile, save_sache)

uplink_period = 60
beacon_time = int(timeslots / 6)
#network.plot_heatmapSF_ULperiods(uplink_period, True, 50)
#network.solve_scheduling("1D")
#network.solve_scheduling("2D")
#network.solve_scheduling("distributed")
#network.solve_scheduling("lrfhss")


sizes = np.linspace(100,3000,5,dtype=int)
network.run_simulation(sizes, "1D")

#network.solve_scheduling_per_beacon(300, beacon_time)

#network.solve_distributed_scheduling(200, beacon_time)

