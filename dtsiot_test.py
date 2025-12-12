from src.base import *
np.random.seed(42)

points = [
    (48.16506850944985, -3.5833598413239546),
    (48.667165569993934, 4.977622353048859),
    (46.907793438371776, 1.38067874956546355),
    (42.79516320966049, 2.3097125314976026),
    (50.716059725651, 2.2728539240359815)
]

ts = load.timescale()
t0 = ts.utc(2025,10,24,17,40)  # 15  16
t1 = ts.utc(2025,10,24,18,00)  # 22  19
delta = 10

satname = 'KINEIS-1A'
altitude_degrees = 10.0
lat, lon = points[0]
point = wgs84.latlon(lat, lon)

#plot_elevationangles(satname, points, t0, t1, delta, altitude_degrees)

#plot_elevationangles_constellation(KINEIS_CONSTELLATION, point, t0, t1, delta)

#plot_dopplereffect(satname, lat, lon, t0, t1, delta, altitude_degrees)

#plot_enddevices(points)

#plot_best_satellite_passes(satname, points, t0, t1)

#plot_sat_track(satname, points, t0, t1, delta)

#plot_sat_track_constellation(KINEIS_CONSTELLATION, points, t0, t1, delta)

#animate_constellation_groundtrack(KINEIS_CONSTELLATION, t0, t1, output_filename='constellation_track4.gif', fps=15, delta=delta)

#animate_constellation_groundtrack_generic(STARLINK_CONSTELLATION2, t0, t1, output_filename='starlink_track3.gif', fps=15, delta=delta)

#plot_alllaps_SFcurve(satname, points, t0, t1)

#plot_sat_altitude(satname, t0, t1, delta)

#get_bestSF_coverage_time(satname, lat, lon, t0, t1)

#plot_toa()

#print_toa()

#max_tx_count()

#plot_lora_linkbudget()

#write_locations(3000, "locations3k.txt")

#plot_best_SFcurve(satname, points, t0, t1, COLORS1)

#print(round(max_sf12_range()/1e3))

#print(get_beta_angle())

plot_doppler_curves(True)
