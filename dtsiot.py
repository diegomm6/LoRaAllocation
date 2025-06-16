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
                        'KINEIS-2A', 'KINEIS-2B', 'KINEIS-2C', 'KINEIS-2D', 'KINEIS-2E',
                        'KINEIS-3A', 'KINEIS-3B', 'KINEIS-3C', 'KINEIS-3D', 'KINEIS-3E',
                        'KINEIS-4A', 'KINEIS-4B', 'KINEIS-4C', 'KINEIS-4D', 'KINEIS-4E',
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
    '#2F4F4F',    # Dark Slate Gray
    '#FF0300',    # Red2
    '#00FF03',    # Lime2
    '#0003FF',    # Blue2
    '#FF03FF',    # Magenta2
    '#03FFFF',    # Cyan2
    '#FFA503',    # Orange2
    '#800380',    # Purple2
    '#008003',    # Green2
    '#FFD703',    # Gold2
    '#FF69BF',    # Hot Pink2
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

plot_sat_track(points, t0, t1)

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

exit(1)

t0 = ts.utc(2024,12,1,7,30,48)
t1 = ts.utc(2024,12,1,7,32,48)
numDevices = 20
slottime = 1 # lora_toa(PL_BYTES, 11)
timeslots = int(np.ceil(round(float(t1 - t0) * 86400) / slottime))

network = DtSIoTNetwork(numDevices, t0, slottime, timeslots, 1, 1)
network.plot_bestSF_map()
network.plot_heatmapSF()
network.plot_bestSF_ocurrences()
network.plot_availableSF_map(11)

