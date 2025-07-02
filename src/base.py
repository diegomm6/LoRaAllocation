import numpy as np
import matplotlib.pyplot as plt
import random, math, time, os, json
from matplotlib import colors
from matplotlib.animation import FuncAnimation, PillowWriter
from geopy.geocoders import Nominatim
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from skyfield.api import load, wgs84
from datetime import datetime, timedelta
from scipy.special import i0  # Modified Bessel function of first kind


KINEIS_CONSTELLATION = ['KINEIS-1A', 'KINEIS-1B', 'KINEIS-1C', 'KINEIS-1D', 'KINEIS-1E',
                        'KINEIS-2A', 'KINEIS-2B', 'KINEIS-2C', 'KINEIS-2D', 'KINEIS-2E',
                        'KINEIS-3A', 'KINEIS-3B', 'KINEIS-3C', 'KINEIS-3D', 'KINEIS-3E',
                        'KINEIS-4A', 'KINEIS-4B', 'KINEIS-4C', 'KINEIS-4D', 'KINEIS-4E',
                        'KINEIS-5A', 'KINEIS-5B', 'KINEIS-5C', 'KINEIS-5D', 'KINEIS-5E']

COLORS1 = [u'#1f77b4', u'#ff7f0e', u'#2ca02c', u'#d62728', u'#9467bd',
           u'#8c564b', u'#e377c2', u'#7f7f7f', u'#bcbd22', u'#17becf']

COLORS2 = [
    '#FF0000',    # Red
    '#00FF00',    # Lime
    '#0000FF',    # Blue
    '#00FFFF',    # Cyan
    '#00CED1',    # Dark Turquoise
    '#FF69B4',    # Hot Pink
    '#FF00FF',    # Magenta
    '#FFA500',    # Orange
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

###############################################################################
##############################  GLOBAL VARIABLES  #############################
###############################################################################

EARTH_G     = 9.80665      # earth gravitational constant in m/s2
EARTH_R     = 6371000      # earth radius in m
SAT_H       = 635000       # satellite altitude in m
LIGHT_C     = 299792458    # speed of light in m/s
CHANNEL_FC  = 868100000    # channel carrier freq in hz
#CHANNEL_FC  = 1.9e9        # S band
HDR_TIME    = 0.233472     # LR-FHSS header time in seconds
FRG_TIME    = 0.1024       # LR-FHSS fragment time in seconds
BCN_TIME    = 120          # beacon window time in seconds

SAT_R = EARTH_R + SAT_H                                  # satellite orbital radius in m
SAT_V = np.sqrt( EARTH_G*EARTH_R / (1 + SAT_H/EARTH_R) ) # satellite velocity in m/s
SAT_W = SAT_V / SAT_R                                    # satellite angular velocity in angles/s

PL_BYTES = 20     # Payload bytes 
LORA_BW = 125000   # LoRa Bandwidth in hz
LR_SENSITIVITY = [-124.5, -127, -129.5, -132, -134.5, -137]  # sensitivity thresholds for 125 khz BW

MAX_PL_LORA = [230, 230, 123 ,59, 59, 59]
MAX_PL_LRFHSS = [58, 123]

GAIN_TX     = 0      # transmitter antenna gain in db
GAIN_RX     = 3      # receiver antenna gain in db
TX_POWER    = 14     # transmitted power in db

SINR_TH = [-6, -9, -12, -15, -17.5, -20] # SINR thresholds for 125 khz BW in dB

ALPHA = 2.5     # path loss exponent
F = 6.0         # bd,  noise figure
AWGN_VAR_DB = -174 + F + 10 * np.log10(LORA_BW)  # Noise power in dBm


# France coordinates limits in degrees
FR_N = 51.05
FR_S = 42.20
FR_E = -4.47
FR_W = 8.13

FR_AREA = 543940 *1e6  # area of France in m2
FR_L    = 500 *1e3     # France shape in m, aproximated to a circle

###############################################################################
##############################  COMMON FUNCTIONS  #############################
###############################################################################

def dBm2W(dBm):
    return np.power(10, (dBm/10)) * 1e-3

def dBm2mW(dBm):
    return np.power(10, (dBm/10))

def mW2dBm(mW):
    return 10 * np.log10(mW)

def calculate_overlap(p1, toa1, p2, toa2, slottime):

    overlap_start = max(p1, p2)
    overlap_end = min(p1 + toa1, p2 + toa2)

    return max(0, overlap_end - overlap_start) * slottime


###############################################################################
##########################  LORA & LR-FHSS FUNCTIONS  #########################
###############################################################################


# lora datarate
# default coding rate is 4/5
def datarate(sf, bw, cr=0.8):
    return sf * bw * cr / (2**sf)


# Coding rate (4/5 = 1, 4/6 = 2, etc.)
def lora_toa(payload_length, sf, ldro=0, coding_rate=1, preamble_length=8, has_header=True):
    """
    Calculate LoRa Time on Air (ToA)
    """
    
    # Symbol time
    Tsym = (2**sf) / LORA_BW
    
    # Preamble time
    Tpreamble = (preamble_length + 4.25) * Tsym
    
    # Low Data Rate Optimization (LDRO)
    ldro = 1 if sf >= 11 else 0
    
    # Header time (if explicit header mode)
    if has_header:
        Theader = math.ceil(20 / (sf - 2)) * Tsym
    else:
        Theader = 0
    
    # Payload symbols calculation
    Npayload = max(8 * payload_length - 4 * sf + 28 + 16, 0)
    Npayload = math.ceil(Npayload / (4 * (sf - 2 * ldro))) * (coding_rate + 4)
    
    # Payload time
    Tpayload = Npayload * Tsym
    
    # Total time on air
    ToA = Tpreamble + Theader + Tpayload
    
    return ToA


def numLRFHSSHops(payload_length: int, CR: int) -> int:
    """
    Calculate the number of frequency hops for the payload
    as a function of its size and the coding rate
    """

    length_bits = ( payload_length + 2 ) * 8 + 6
    length_bits *= (3/CR)

    nb_hops_out = ( length_bits + 47 ) // 48  # can be just ceil(bits/48)

    return nb_hops_out


def lrfhss_toa(payload_length: int, CR: int) -> float:

    numHeaders = 3 if CR == 1 else 2
    numFragments = numLRFHSSHops(payload_length, CR)

    return HDR_TIME * numHeaders + FRG_TIME * numFragments



def print_toa():
    print(f'For {PL_BYTES} bytes payload:')
    for sf in range(7, 13): print(f'sf{sf} : {1000*lora_toa(20, sf)} ms')
    for cr in [1,2]: print(f'cr{cr} : {1000*lrfhss_toa(20, cr)} ms')


# define the duration of the transmission for each SF
# method double defines SF7 as 1 timeslot and doubles it for the next one DEPRECATED
# method exact also defines SF7 as 1 and calculates the rest based on ToA
# a unit slot is defined as slottime seconds 
def get_timeslots_perSF(slottime):

    #if method=='double':
    #    return [2**sf for sf in range(6)]

    all_ToA = [lora_toa(PL_BYTES, sf) for sf in [7,8,9,10,11,12]]

    sf_slots = [1]
    for toa in all_ToA[1:]:
        sf_slots.append(int(np.ceil(toa / slottime)))

    return sf_slots

    
# time on air in timeslots for LR-FHSS CR2/3 and CR1/3, that order
def get_timeslots_perCR(slottime):

    all_ToA = [lrfhss_toa(PL_BYTES, cr) for cr in [2,1]]
    cr_slots = [int(np.ceil(toa / slottime)) for toa in all_ToA]
    return cr_slots


# LoRa success probality accordint to paper
# "Packet Collision Probability of Direct-to-Satellite IoT Systems"
def LoRA_success_prob(sf, numNodes):

    density = numNodes / FR_AREA  # nodes per square meter
    ToA = lora_toa(PL_BYTES, sf)  # time on air in seconds

    return np.exp(- 4 * FR_L * ToA * SAT_V * density)


# get maximum number of ED such the success is at given threshold
def max_num_ED(sf, threshold=.5):    
    ToA = lora_toa(PL_BYTES, sf)  # time on air in seconds
    numerator = FR_AREA * np.log(1 / threshold)
    denominator = 4 * FR_L * ToA * SAT_V

    return numerator / denominator

def max_nodes_for_success(sf, min_success_prob):

    ToA = lora_toa(PL_BYTES, sf)  
    numerator = FR_AREA * np.log(1 / min_success_prob)
    denominator = 4 * FR_L * ToA * SAT_V

    return numerator / denominator


# Doppler rate success check, LR-FHSS defined as SF13
def doppler_rate_success(dopplerrate, sf):

    # LR-FHSS is inmune to doppler
    if sf==13 or sf==14: return True

    ldro = 1 if sf >= 11 else 0
    toa = lora_toa(PL_BYTES, sf)
    freq_variation_limit = LORA_BW / (3 * 2**sf)

    if ldro:
        freq_variation_limit *= 16

    return (abs(toa * dopplerrate) < freq_variation_limit)

def doppler_shift_success(dopplershift, sf):
    # LR-FHSS is inmune to doppler
    if sf==13 or sf==14: return True

    return (abs(dopplershift) < LORA_BW/4)


# Link budget success check
# LR-FHSS CR2/3 defined as SF13 and CR1/3 as SF14
def linkbudget_success(receivedpower, sf):

    # define CR2/3 coverage as SF11
    if sf==13: return receivedpower > LR_SENSITIVITY[4]
    
    # define CR1/3 coverage as SF12
    if sf==14: return receivedpower > LR_SENSITIVITY[5]
    
    return receivedpower > LR_SENSITIVITY[sf-7]


def get_available_sf(dopplershift, dopplerrate, P_r):

    sf_availability = []
    for sf in [7,8,9,10,11,12,13,14]:
        
        if doppler_rate_success(dopplerrate, sf) and \
            doppler_shift_success(dopplershift, sf) and \
                linkbudget_success(P_r, sf):
            sf_availability.append(1)
        
        else:
            sf_availability.append(0)

    return sf_availability


def get_best_sf(availableSF):

    for sf, is_available in enumerate(availableSF):
        if is_available:
            return sf + 7
        
    return 0


###############################################################################
###############################  CHANNEL MODELS  ##############################
###############################################################################

# Free Space Path Loss (FSPL) in W
def fspl_w(distance):
    return dBm2mW(GAIN_TX) * dBm2mW(GAIN_RX) * (LIGHT_C / (4 * np.pi * CHANNEL_FC * distance)) ** 2

# Free Space Path Loss (FSPL) in dB
def fspl_dB(distance, frequency):
    return 20 * np.log10(distance) + 20 * np.log10(frequency) + 20 * np.log10(4 * np.pi / LIGHT_C)


def max_sf12_range():
    effective_power = TX_POWER + GAIN_TX + GAIN_RX - LR_SENSITIVITY[5]
    term = effective_power - 20 * np.log10(CHANNEL_FC) - 20 * np.log10(4 * np.pi / LIGHT_C)
    return 10 ** (term / 20)


# Received power calculation function
def received_power(distance):
    return TX_POWER + GAIN_TX + GAIN_RX - fspl_dB(distance, CHANNEL_FC)


def getSNR():

    distances = np.linspace(630000, 2800000, 100)
    r_alpha_tx = np.power(distances, -ALPHA)

    num_samples = 1000
    for m in range(6):
        
        success_count = np.zeros(len(distances), dtype=np.float64)
        for i in range(num_samples):
            g_tx = np.random.exponential(scale=1.0, size=len(distances))
            signal = np.multiply(g_tx, r_alpha_tx)
            interference_noise = dBm2W(AWGN_VAR_DB) / dBm2W(TX_POWER)
            
            snr = mW2dBm(signal / interference_noise)
            success_count += (snr > SINR_TH[m]).astype(np.float64)  # Convert boolean to float
        
        success_prob = success_count / num_samples  # Now valid float division

        plt.plot(distances/1e3, success_prob, label=f'SF{m+7}')

    plt.xlabel('distance [km]')
    plt.ylabel('success probability')
    plt.title(f'Success probability (SNR>threshold) with alpha={ALPHA}')
    plt.legend()
    plt.grid()
    plt.show()

def getSINR():

    distance = 1e3 # 1000km, same distance for both signals
    r_alpha_tx = np.power(distance, -ALPHA)
    max_num_interferences = 10
    runs = 5000

    noise = dBm2W(AWGN_VAR_DB) / dBm2W(TX_POWER)
    print(f'noise: {mW2dBm(noise*1e3)} dBm')

    total_success = []

    for m in range(6):
        total_success = []
        for interferers in range(1, max_num_interferences + 1):
            success = 0
            for r in range(runs):

                signal = np.random.exponential(scale=1.0) * r_alpha_tx

                interference = 0
                for i in range(interferers):
                    interference += np.random.exponential(scale=1.0) * r_alpha_tx

                sinr = signal / (interference + noise)
                sinr_tx = mW2dBm(sinr)

                if (sinr_tx >= SINR_TH[m]):
                    success +=1

            total_success.append(success / runs)

        plt.plot(range(1, max_num_interferences + 1), total_success, marker='o', label=f'SF{m+7}')

    plt.xlabel('number of concurrent interferers')
    plt.ylabel('success probability for reference signal')
    plt.title(f'Success probability for each SF considering SINR thresholds')
    plt.legend()
    plt.grid()
    plt.show()

    #print(f'signal: {signal}, interference: {interference}, noise: {noise}')


# Channel model parameters (from Table I)
K_coeff = [2.731, -0.10474, -0.002774]
mu_coeff = [-2.331, 0.1142, -0.001939, -0.00001094]
sigma_coeff = [4.5, -0.05]

def rice_fading_sample(K, S):
    """Generate Rice-distributed sample given K-factor and shadowing S"""
    v = S * np.sqrt(K/(K+1))   # Non-centrality parameter
    sigma_r = S / np.sqrt(2*(K+1))  # Scale parameter
    # Generate complex Gaussian components
    X = v + sigma_r * np.random.randn()
    Y = sigma_r * np.random.randn()
    return np.sqrt(X**2 + Y**2)


def getSNR2():

    elevation_angles = np.linspace(0, np.pi/2, 100)  # Elevation angles from 0 to 90 degrees
    distances = dist2sat_angle(elevation_angles)
    num_samples = 1000
    
    K_vals = K_coeff[0] + K_coeff[1]*elevation_angles + K_coeff[2]*np.power(elevation_angles,2)
    mu_vals = (mu_coeff[0] + mu_coeff[1]*elevation_angles + 
               mu_coeff[2]*np.power(elevation_angles,2)**2 + mu_coeff[3]*np.power(elevation_angles,3))
    sigma_vals = sigma_coeff[0] + sigma_coeff[1]*elevation_angles
    
    # Path loss (free-space)
    path_loss = fspl_w(distances)
    
    # Noise power
    noise_power_W = dBm2W(AWGN_VAR_DB)
    
    for m in range(6):
        success_count = np.zeros(len(distances))
        for _ in range(num_samples):
            # Log-normal shadowing (dB)
            S_dB = np.random.normal(loc=mu_vals, scale=sigma_vals)
            S_linear = 10**(S_dB/20)  # Convert to linear
            
            # Generate Ricean fading samples
            h = np.zeros(len(distances))
            for i, (K, S_lin) in enumerate(zip(K_vals, S_linear)):
                h[i] = rice_fading_sample(K, S_lin)
            
            # Received power
            rx_power = TX_POWER * path_loss * h**2
            
            # SNR calculation
            snr_dB = mW2dBm(rx_power / noise_power_W)
            success_count += (snr_dB > SINR_TH[m]).astype(float)
        
        success_prob = success_count / num_samples
        plt.plot(distances/1e3, success_prob, label=f'SF{m+7}')
    
    plt.xlabel('Distance [km]')
    plt.ylabel('Success Probability')
    plt.title('Success Probability (SNR > Threshold) with Composite Fading')
    plt.legend()
    plt.grid()
    plt.show()


###############################################################################
############################  SATELLITE FUNCTIONS  ############################
###############################################################################

# ground to satellite distance as a function of the elevation angle Eangle
def dist2sat_angle(Eangle):
    return EARTH_R * ( np.sqrt((SAT_R / EARTH_R)**2 - (np.cos(Eangle))**2) - np.sin(Eangle) )

# ground to satellite distance as a function of time
# at t=0 the satellite is located at the maximum elevation angle maxE
def dist2sat_time(maxE, time):
    a0 = np.arccos(EARTH_R * np.cos(maxE) / SAT_R) - maxE
    return np.sqrt(EARTH_R**2 + SAT_R**2 - 2 * SAT_R * EARTH_R * np.cos(a0) * np.cos(SAT_W * time))

# distance from device to projection of the satellite on ground
def ground_distance(Eangle):
    return EARTH_R * np.arcsin( dist2sat_angle(Eangle)*np.cos(Eangle) / (EARTH_R+SAT_H) )


# calculate instantaneous doppler shift and doppler rate
# at time t and for a node with maximum elevation angle maxE
def doppler(maxE, t):

    a0 = np.arccos(EARTH_R*np.cos(maxE) / SAT_R) - maxE
    x = SAT_R*EARTH_R * np.cos(a0)

    dist = np.sqrt(EARTH_R**2 + SAT_R**2 - 2*x * np.cos(SAT_W*t))

    d_dist_dt = SAT_W*x * np.sin(SAT_W*t) / dist

    doppler_shift = -CHANNEL_FC * d_dist_dt / LIGHT_C
    doppler_rate = -CHANNEL_FC * SAT_W*x * (dist * SAT_W * np.cos(SAT_W*t) - np.sin(SAT_W*t) * d_dist_dt) / (LIGHT_C * dist**2)

    return [doppler_shift, doppler_rate]


# return KINEIS-1A satellite as EarthSatellite module
def load_satellite(satname='KINEIS-1A'):
    station_url = f'https://celestrak.org/NORAD/elements/gp.php?NAME=KINEIS&FORMAT=TLE'
    stations = load.tle_file(station_url)
    by_name = {sat.name: sat for sat in stations}
    satellite = by_name[satname]
    return satellite


# return a random uniformly distributed point in France as lat, lon coordinates
def get_random_latlon():

    app=Nominatim(user_agent="JournalDEv")
    x, y = random.uniform(FR_S, FR_N), random.uniform(FR_E, FR_W)
    try:
        location = app.reverse(str(x)+","+str(y), timeout=None)
        time.sleep(0.2)
        if location !=None:
            address = location.raw['address']
            country = address.get('country',"")
            if country == 'France':
                return x,y

    except Exception as error: pass
    else: return get_random_latlon()
    finally: pass


# Writing locations to file
def write_locations(num_locations, filename="locations.txt"):
    with open(filename, 'w') as f:
        for i in range(num_locations):
            if i%100==0: print(f'done for {i}')
            lat, lon = get_random_latlon()
            f.write(f"{lat},{lon}\n")

# Reading locations from file
def read_locations(filename="locations.txt"):
    locations = []
    with open(filename, 'r') as f:
        for line in f:
            lat, lon = map(float, line.strip().split(','))
            locations.append((lat, lon))
    return locations


# return a list of tuples where each element represent a LOS connection
# between the satellite and a given point with lat, lon coordinates
# during the time window [t0, t1]
# a tuple is composed as (rise_time, culminate_time, set_time)
def get_satellite_events(point, t0, t1, altitude_degrees):

    satellite = load_satellite()
    t, events = satellite.find_events(point, t0, t1, altitude_degrees=altitude_degrees)

    satellite_passes = []
    rise_time = 0
    culminate_time = 0

    for ti, event in zip(t, events):

        if event==0: 
            rise_time = ti
        if event==1: 
            culminate_time = ti
        if event==2: 
            satellite_passes.append([rise_time, culminate_time, ti])
        
        #print(ti.utc_strftime('%Y %b %d %H:%M:%S'), event_names[event])

    return satellite_passes


# returns the elevation, range, doppler shift, doppler rate and time vector
# for a given point with lat, lon coordinates during the time window [t0, t1]
def get_dopplereffect(point, t0, t1, deltatime=1):

    satellite = load_satellite()
    difference = satellite - point

    times = []
    elevation = []
    ranges = []
    doppler_shifts = []
    t = t0
    while t < t1:

        topocentric = difference.at(t)
        alt, _, _ = topocentric.altaz()
        _, _, range_, _, _, range_rate = topocentric.frame_latlon_and_rates(point)

        times.append(t.utc_datetime())
        t += timedelta(seconds=deltatime)

        if alt.degrees < 0:
            elevation.append(np.NaN)
            ranges.append(np.NaN)
            doppler_shifts.append(np.NaN)

        else:
            elevation.append(alt.degrees)
            ranges.append(range_.m)
            doppler_shifts.append(- CHANNEL_FC * range_rate.m_per_s / LIGHT_C)


    doppler_rates = np.gradient(doppler_shifts) / np.gradient([time.timestamp() for time in times])

    return elevation, times, ranges, doppler_shifts, doppler_rates


def get_bestSF_coverage_time(lat, lon, t0, t1):

    point = wgs84.latlon(lat, lon)
    satellite_passes = get_satellite_events(point, t0, t1, altitude_degrees=0.0)

    total_laps = len(satellite_passes)
    total_coverage_time = []
    total_coverage_time_per_sf = np.zeros((total_laps, 7))

    for i, lap in enumerate(satellite_passes):

        rise_time = lap[0]
        set_time = lap[2]

        elevation, times, ranges, doppler_shifts, doppler_rates = get_dopplereffect(point, rise_time, set_time)

        rcvd_powers = [received_power(range_) for range_ in ranges]
        bestSfs = [get_best_sf(shift, rate, P_r) for shift, rate, P_r in zip(doppler_shifts, doppler_rates, rcvd_powers)]

        total_coverage_time.append((times[-1] - times[0]).total_seconds())

        last_t = times[0]
        last_sf = bestSfs[0]
        for t, sf in zip(times, bestSfs):

            if sf != last_sf:
                total_coverage_time_per_sf[i][sf-7] += (t - last_t).total_seconds()
                last_t = t
                last_sf = sf


    for i in range(total_laps):
        #print(f"\nlap {i} time: {total_coverage_time[i]} s")
        total_coverage_time = 0

        for sf in [7,8,9,10,11,12]:
            total_coverage_time += total_coverage_time_per_sf[i][sf-7]
            print(f"SF{sf} total coverage time: {total_coverage_time_per_sf[i][sf-7]} s")

        print(f"lap {i} time: {total_coverage_time} s\n")



###############################################################################
#############################  PLOTTING FUNCTIONS  ############################
###############################################################################

def plot_lora_success_prob():

    sizes = np.linspace(1, 2500, 1000)
    plt.figure(figsize=(12, 8))
    for sf in range(7, 13):
        prob = LoRA_success_prob(sf, sizes)
        plt.plot(sizes, prob, label=f'SF{sf}')

    plt.title('LoRa Success Probability vs Network Size', fontsize=16)
    plt.xlabel('Network size [nodes]', fontsize=14)
    plt.ylabel('Success Probability P(S)', fontsize=14)
    plt.xscale('log')
    plt.legend(title='LoRa SF')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.show()


def plot_max_lora_nodes():
    
    thresholds = np.linspace(0.01, 0.99, 100)  # Avoid 0 and 1 for numerical stability
    plt.figure(figsize=(12, 8))
    
    for sf in range(7, 13):
        max_nodes = [max_nodes_for_success(sf, p) for p in thresholds]
        plt.plot(thresholds, max_nodes, label=f'SF{sf}')
    
    plt.title('Maximum Nodes vs Success Probability Threshold', fontsize=16)
    plt.xlabel('Success Probability Threshold', fontsize=14)
    plt.ylabel('Maximum Number of Nodes', fontsize=14)
    plt.yscale('log')  # Log scale for better visualization
    plt.legend(title='LoRa SF')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.show()


# Plotting Time on Air for different Spreading Factors
def plot_toa():

    plt.figure(figsize=(12, 8))

    for sf, max_pl in zip(range(7, 13), MAX_PL_LORA):
        payload_bytes = np.arange(1, max_pl)
        time_on_air = [lora_toa(int(x), sf) for x in payload_bytes]
        plt.plot(payload_bytes, time_on_air, label=f'SF{sf}')

    for CR, max_pl in zip([1,2], MAX_PL_LRFHSS):
        payload_bytes = np.arange(1, max_pl)
        time_on_air = [lrfhss_toa(int(x), CR) for x in payload_bytes]
        plt.plot(payload_bytes, time_on_air, label=f'LR-FHSS {CR}/3')

    # Plot settings
    plt.title('LoRa and LR-FHSS Time on Air vs Payload Size\n(LoRa BW=125 kHz)', fontsize=16)
    plt.xlabel('Payload Size [bytes]', fontsize=14)
    plt.ylabel('Time on Air [seconds]', fontsize=14)
    plt.legend(title='LoRa SF / LR-FHSS CR')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    #plt.show()
    plt.savefig("img/timeonair.pdf")


def max_tx_count(num_channels=1):

    plt.figure(figsize=(12, 8))

    for sf, max_pl in zip(range(7, 13), MAX_PL_LORA):
        payload_bytes = np.arange(1, max_pl)
        time_on_air = np.array([lora_toa(int(x), sf) for x in payload_bytes])
        max_tx = num_channels * np.floor(BCN_TIME / time_on_air)
        plt.plot(payload_bytes, max_tx, label=f'SF{sf}')

    plt.title(f'Maximum TX per SF with {num_channels} channels \n(LoRa BW=125 kHz)', fontsize=16)
    plt.xlabel('Payload Size [bytes]', fontsize=14)
    plt.ylabel('Transmission', fontsize=14)
    plt.legend(title='LoRa SF / LR-FHSS CR')
    plt.grid(True, linestyle='--', alpha=0.7)
    #plt.xlim(0, 50)
    #plt.ylim(0, 2000)
    plt.tight_layout()
    #plt.show()
    plt.savefig("img/maxtx2.png")


def plot_visibility_vs_position():

    minEangle = 20 * np.pi /180
    maxRange = dist2sat_angle(minEangle)
    maxGround_dist = EARTH_R * np.arcsin( maxRange*np.cos(minEangle) / (EARTH_R+SAT_H) )

    #elevation_angles = np.array([1, 10, 20, 30, 40, 50, 60, 70, 80, 89])
    elevation_angles = np.array([20, 30, 40, 50, 60, 70, 80, 89])
    slant_ranges = dist2sat_angle(elevation_angles * np.pi / 180)
    ground_distances = EARTH_R * np.arcsin(slant_ranges * np.cos(elevation_angles * np.pi / 180) / (EARTH_R + SAT_H))

    theta_angles = np.linspace(90, 270, 200)
    
    plt.figure(figsize=(10, 6))

    for e, d in zip(elevation_angles, ground_distances):

        x = d * np.cos(theta_angles * np.pi / 180)
        y = d * np.sin(theta_angles * np.pi / 180)

        visibility_times = (y + np.sqrt(np.power(maxGround_dist,2) - np.power(x,2))) / SAT_V
        plt.plot(theta_angles-90, visibility_times, label=f'E={e}°')


    plt.xlabel('theta angle [°]', fontsize=14)
    plt.ylabel('Visibility times [s]', fontsize=14)
    plt.yticks(fontsize=12)
    plt.xticks(fontsize=12)
    plt.legend(title='Elevation angles', fontsize=12, title_fontsize='13')
    plt.title('Visibility times vs theta angles for different E angles', fontsize=14)
    plt.grid()
    plt.show()
 

def plot_lora_linkbudget():

    # Elevation angles and corresponding distances (in meters)
    elevation_angles = np.arange(10, 91, 1)   # Elevation angles from 10° to 90°
    distances = dist2sat_angle(np.radians(elevation_angles))

    # Calculate received power for different configurations
    P_r = received_power(distances)

    plt.figure(figsize=(10,6))
    plt.plot(elevation_angles, P_r, color='red')

    plt.axhline(y=-124.5, color='gray', linestyle=':', label=f'SF7 Sensitivity')
    plt.axhline(y=-127, color='gray', linestyle='-.', label=f'SF8 Sensitivity')
    plt.axhline(y=-129.5, color='gray', linestyle='--', label=f'SF9 Sensitivity')
    plt.axhline(y=-132, color='gray', linestyle='-', label=f'SF10 Sensitivity')
    plt.axhline(y=-134.5, color='gray', linestyle=(0, (3, 1, 1, 1)), label=f'SF11 Sensitivity')
    plt.axhline(y=-137, color='gray', linestyle=(0, (5, 10)), label='SF12 Sensitivity')

    plt.title('Received Power vs Elevation Angle with FSPL', fontsize=14)
    plt.xlabel('Elevation Angle (degrees)', fontsize=12)
    plt.ylabel('Received Power (dBm)', fontsize=12)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
    #plt.savefig("linkbudget.pdf")


# example:
# maxE_list = [15, 30, 45, 60, 90] 
# plot_bestSFcurve(maxE_list, 200)
def plot_bestSFcurve(maxE_list, num_samples):
    """
    Plot multiple scatter plots for different maxE values on the same figure, 
    each with a distinct marker.
    """
    
    markers = ['o', 's', '^', 'D', 'P', '*', 'v']  # List of distinct markers
    cmap = plt.cm.rainbow
    bounds = np.arange(7, 14)  # Boundaries for SF values (7 to 12)
    norm = colors.BoundaryNorm(bounds, cmap.N)
    
    plt.figure(figsize=(10, 6))
    
    for i, maxE_deg in enumerate(maxE_list):
        maxE = np.radians(maxE_deg)  # Convert degrees to radians
        
        # Calculate distance, angles, and time
        dist = dist2sat_angle(maxE)
        alpha_angle = np.arcsin(np.multiply(dist, np.cos(maxE)) / SAT_R)
        max_alpha_angle = np.arcsin(EARTH_R * np.sqrt((SAT_R / EARTH_R)**2 - 1) / SAT_R)
        ground_tracks = EARTH_R * np.sqrt(max_alpha_angle**2 - np.power(alpha_angle, 2))
        tau = ground_tracks / SAT_V

        Eangles = []
        bestSfs = []
        time = np.linspace(-tau, tau, num_samples)

        for t in time:
            distance = np.sqrt(EARTH_R**2 + SAT_R**2 - 2 * SAT_R * EARTH_R * np.cos(SAT_W * t) * np.cos(alpha_angle))
            dopplerdata = doppler(maxE, t)
            dopplershift = dopplerdata[0]
            dopplerrate = dopplerdata[1]

            P_r = received_power(distance)

            Eangles.append(np.arcsin((SAT_H**2 + 2 * SAT_H * EARTH_R - distance**2) / (2*distance * EARTH_R)) * 180 / np.pi)
            bestSfs.append(get_best_sf(dopplershift, dopplerrate, P_r))

        # Scatter plot with distinct markers for each maxE
        plt.scatter(time, Eangles, c=bestSfs, cmap=cmap, norm=norm, marker=markers[i % len(markers)], label=f'maxE={maxE_deg}°')


    # Add colorbar with custom ticks
    tick_positions = (bounds[:-1] + bounds[1:]) / 2
    cbar = plt.colorbar(ticks=tick_positions)
    cbar.set_label('SF')
    cbar.ax.set_yticklabels([str(int(tick)) for tick in bounds[:-1]])

    plt.xlabel('Time [s]')
    plt.ylabel('Elevation angle [°]')
    plt.title(f'Lora best SF during satellite pass for multiple maxE values')
    plt.legend()
    plt.grid()
    plt.show()


# oudated simplified model, no satellite orbit
def plot_doppler_curves(shift):

    num_samples = 1000
    maxE_angles = np.array([90, 60, 30, 15, 5, 1]) * np.pi / 180

    dist = dist2sat_angle(maxE_angles)

    alpha_angles = np.arcsin(np.multiply(dist, np.cos(maxE_angles)) / SAT_R)

    max_alpha_angle = np.arcsin(EARTH_R * np.sqrt((SAT_R/EARTH_R)**2 - 1) / SAT_R)

    ground_tracks = EARTH_R * np.sqrt(max_alpha_angle**2 - np.power(alpha_angles,2))
    visibility_time = ground_tracks / SAT_V

    plt.figure()
    for maxE, tau in zip(maxE_angles, visibility_time):

        time = np.linspace(-tau, tau, num_samples)
        dopplerdata = np.array([doppler(maxE, t) for t in time])

        if shift:
            plt.plot(time, dopplerdata[:,0]/1e3, label=f'θ* = {round(maxE*180/np.pi)}°')
        else:
            plt.plot(time, dopplerdata[:,1], label=f'θ* = {round(maxE*180/np.pi)}°')

    if shift:
        plt.ylabel('Doppler Shift [kHz]')
        plt.title('Doppler Shift versus maximum elevation angle θ*')

    else:
        plt.ylabel('Doppler Rate [Hz/s]')
        plt.title('Doppler Rate versus maximum elevation angle θ*')

    plt.xlabel('time [s]')
    plt.legend()
    plt.grid()
    #plt.savefig("dopplerShift.jpg")
    plt.show()


###############################################################################
###############################################################################


def plot_enddevices(points):

    latitudes = [point[0] for point in points]
    longitudes = [point[1] for point in points]

    plt.figure(figsize=(10, 5))
    ax = plt.axes(projection=ccrs.Robinson())
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.gridlines(draw_labels=True)

    ax.scatter(longitudes, latitudes, color='red', s=50, transform=ccrs.PlateCarree(), label='Locations')

    ax.set_extent([FR_E-.5, FR_W+.5, FR_S-.5, FR_N+.5], crs=ccrs.PlateCarree())
    plt.legend()
    plt.title('Locations on Mercator Projection')
    plt.show()


def plot_sat_altitude(t0, t1, delta):

    times = []
    heights = []
    satellite = load_satellite()
    t = t0
    while t < t1:
        sat = satellite.at(t)
        height = wgs84.height_of(sat)
        heights.append(height.km)
        times.append(t.utc_datetime())
        t += timedelta(seconds=delta)

    plt.plot(times, heights)
    plt.title('Satellite Altitude', fontsize=18)
    plt.xlabel('Time [seconds]', fontsize=14)
    plt.ylabel('Altitude [km]', fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(fontsize=10)
    plt.grid()
    plt.show()


def plot_sat_track(points, t0, t1, delta):

    plt.figure(figsize=(16, 8))
    ax = plt.axes(projection=ccrs.Robinson())
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.gridlines(draw_labels=True)

    latitudes = [point[0] for point in points]
    longitudes = [point[1] for point in points]
    ax.scatter(longitudes, latitudes, color='red', s=10, transform=ccrs.PlateCarree(), label='End-Devices')

    satellite = load_satellite()
    sat = satellite.at(t0 - timedelta(seconds=1))
    last_lat, _ = wgs84.latlon_of(sat)
    last_lat = last_lat.degrees
    ascending_labeled = False
    descending_labeled = False
    
    t = t0
    while t < t1:
        sat = satellite.at(t)
        lat, lon = wgs84.latlon_of(sat)
            
        if lat.degrees > last_lat:
            label = 'Sat Ascending' if not ascending_labeled else ''
            plt.scatter(lon.degrees, lat.degrees, color='blue', s=10, transform=ccrs.PlateCarree(), marker='^', label=label)
            ascending_labeled = True
        else:
            label = 'Sat Descending' if not descending_labeled else ''
            plt.scatter(lon.degrees, lat.degrees, color='green', s=10, transform=ccrs.PlateCarree(), marker='v', label=label)
            descending_labeled = True
            
        last_lat = lat.degrees
        t += timedelta(seconds=delta)

    ax.set_global()
    plt.title('Satellite Trajectory for 1 day', fontsize=16)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(fontsize=10)
    plt.show()
    #plt.savefig("sattrack.pdf")


def plot_laptrack(t0, t1, delta):

    satellite = load_satellite()
    latitudes = []
    longitudes = []
    t = t0
    while t < t1:
        sat = satellite.at(t)
        lat, lon = wgs84.latlon_of(sat)
        latitudes.append(lat.degrees)
        longitudes.append(lon.degrees)
        t += timedelta(seconds=delta)

    if latitudes[-1]>latitudes[0]:
        plt.scatter(longitudes, latitudes, color='blue', s=30, transform=ccrs.PlateCarree(), marker='^', label='Sat Ascending')
    else:
        plt.scatter(longitudes, latitudes, color='green', s=30, transform=ccrs.PlateCarree(), marker='v', label='Sat Descending')


def plot_dtsiot_scenario(points, lap_times):

    #plt.figure(figsize=(16, 8))
    ax = plt.axes(projection=ccrs.Robinson())
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.gridlines(draw_labels=True)

    latitudes = [point[0] for point in points]
    longitudes = [point[1] for point in points]
    ax.scatter(longitudes, latitudes, color='red', s=30, transform=ccrs.PlateCarree(), label='End-Devices')

    # plot satellite tracks
    for t0, t1 in lap_times:
        plot_laptrack(t0, t1)

    ax.set_extent([FR_E-10, FR_W+10, FR_S-10, FR_N+10], crs=ccrs.PlateCarree())
    plt.title('Best Satellite Trajectories and End-devices', fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(fontsize=8)
    #plt.show()
    plt.savefig("roi.pdf")


def plot_best_satellite_passes(points, t0, t1):

    all_rise_times_1st = []
    all_set_times_1st = []
    all_rise_times_2st = []
    all_set_times_2st = []
    satellite_passes = []
    for lat, lon in points:

        point = wgs84.latlon(lat, lon)
        altitude_degrees = 30.0
        satellite_passes = get_satellite_events(point, t0, t1, altitude_degrees=altitude_degrees)

        all_rise_times_1st.append(satellite_passes[0][0])
        all_set_times_1st.append(satellite_passes[0][2])

        all_rise_times_2st.append(satellite_passes[1][0])
        all_set_times_2st.append(satellite_passes[1][2])


    lap_times = [(min(all_rise_times_1st),  max(all_set_times_1st)),
                 (min(all_rise_times_2st),  max(all_set_times_2st))]

    plot_dtsiot_scenario(points, lap_times)
    

def plot_elevationangles(points, t0, t1, delta, altitude_degrees):

    satellite = load_satellite()

    for i, (lat, lon) in enumerate(points):

        point = wgs84.latlon(lat, lon)
        satellite_passes = get_satellite_events(point, t0, t1, altitude_degrees=altitude_degrees)
        difference = satellite - point

        for sat_pass in satellite_passes:

            times = []
            distances = []
            elevation = []
            rise_time = sat_pass[0]
            set_time = sat_pass[2]

            t = rise_time
            while t < set_time:

                topocentric = difference.at(t)
                alt, az, distance = topocentric.altaz()
                times.append(t.utc_datetime())
                distances.append(distance.km)
                elevation.append(alt.degrees)
                t += timedelta(seconds=delta)

            plt.plot(times, elevation, color=COLORS1[i]) # label=f'lat={lat:.2f}, lon={lon:.2f}'

    plt.title('Elevation Angle from End-Device to Satellite', fontsize=18)
    plt.xlabel('Time [seconds]', fontsize=14)
    plt.ylabel('Elevation [degrees]', fontsize=14)
    plt.yticks(fontsize=12)
    plt.xticks(fontsize=12)
    plt.legend(fontsize=10)
    plt.grid()
    plt.show()


def plot_elevationangles_constellation(constellation, point, t0, t1, delta):

    for i, satname in enumerate(constellation):

        satellite = load_satellite(satname)
        difference = satellite - point

        times = []
        elevation = []
        t = t0
        while t < t1:

            topocentric = difference.at(t)
            alt, _, _ = topocentric.altaz()

            times.append(t.utc_datetime())
            t += timedelta(seconds=delta)

            if alt.degrees < 0: elevation.append(np.NaN)
            else: elevation.append(alt.degrees)


        plt.plot(times, elevation, color=COLORS2[i]) # label=f'lat={lat:.2f}, lon={lon:.2f}'

    plt.title('Elevation Angle from End-Device to Satellites', fontsize=18)
    plt.xlabel('Time', fontsize=14)
    plt.ylabel('Elevation [degrees]', fontsize=14)
    plt.yticks(fontsize=12)
    plt.xticks(fontsize=12)
    plt.legend(fontsize=10)
    plt.grid()
    plt.show()


def plot_dopplereffect(lat, lon, t0, t1, delta, altitude_degrees):

    satellite = load_satellite()
    point = wgs84.latlon(lat, lon)
    satellite_passes = get_satellite_events(point, t0, t1, altitude_degrees=altitude_degrees)
    difference = satellite - point

    all_times = []
    all_shifts = []
    all_doppler_rates = []

    for lap in satellite_passes:

        times = []
        shifts = []
        rise_time = lap[0]
        set_time = lap[2]

        t = rise_time
        while t < set_time:

            topocentric = difference.at(t)
            _, _, _, _, _, range_rate = topocentric.frame_latlon_and_rates(point)
            shifts.append(- CHANNEL_FC * range_rate.m_per_s / LIGHT_C)
            times.append(t.utc_datetime())
            t += timedelta(seconds=delta)

        doppler_rates = np.gradient(shifts) / np.gradient([time.timestamp() for time in times])

        all_times.append(times)
        all_shifts.append([s / 1000 for s in shifts])
        all_doppler_rates.append(doppler_rates)

    # Create subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # Plot Doppler shifts in kHz
    for times, shifts in zip(all_times, all_shifts):
        ax1.plot(times, shifts)
    ax1.set_title('Doppler Shift')
    ax1.set_ylabel('Shift (kHz)')
    ax1.grid(True)

    # Plot Doppler rates in Hz/s
    for times, doppler_rates in zip(all_times, all_doppler_rates):
        ax2.plot(times, doppler_rates)
    ax2.set_title('Doppler Rate')
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Rate (Hz/s)')
    ax2.grid(True)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def plot_alllaps_SFcurve(points, t0, t1):
    """
    Plot multiple scatter plots for different maxE values on the same figure, 
    each with a distinct marker.
    """
    
    markers = ['1', '|', 'd', 'x', '+'] 
    cmap = plt.cm.rainbow
    bounds = np.arange(7, 14)  # Boundaries for SF values (7 to 12)
    norm = colors.BoundaryNorm(bounds, cmap.N)
    
    plt.figure(figsize=(14, 8))

    for i, (lat, lon) in enumerate(points):

        point = wgs84.latlon(lat, lon)
        satellite_passes = get_satellite_events(point, t0, t1, altitude_degrees=0.0)

        all_times = []
        all_bestSFs = []
        all_elevations = []

        for lap in satellite_passes:

            rise_time = lap[0]
            set_time = lap[2]

            elevation, times, ranges, doppler_shifts, doppler_rates = get_dopplereffect(point, rise_time, set_time)

            rcvd_powers = [received_power(range_) for range_ in ranges]
            bestSfs = [get_best_sf(shift, rate, P_r) for shift, rate, P_r in zip(doppler_shifts, doppler_rates, rcvd_powers)]

            all_times.append(times)
            all_bestSFs.append(bestSfs)
            all_elevations.append(elevation)

            plt.scatter(times, elevation, c=bestSfs, cmap=cmap, norm=norm, marker=markers[i % len(markers)], label=f'ED={lat:.2f},{lon:.2f}')


    # Add colorbar with custom ticks
    tick_positions = (bounds[:-1] + bounds[1:]) / 2
    cbar = plt.colorbar(ticks=tick_positions)
    cbar.set_label('SF', fontsize=12)
    cbar.ax.tick_params(labelsize=12)
    cbar.ax.set_yticklabels([str(int(tick)) for tick in bounds[:-1]])

    plt.title('Best LoRa SF per End-Device during satellite passes', fontsize=16)
    plt.xlabel('Time', fontsize=14)
    plt.ylabel('Elevation angle [degrees]', fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    #plt.legend(fontsize=10)
    plt.grid()
    plt.show()


def plot_best_SFcurve(points, t0, t1, _colors):
    """
    Plot multiple scatter plots for different maxE values on the same figure, 
    each with a distinct marker.
    """
    
    plt.figure(figsize=(14, 8))

    for i, (lat, lon) in enumerate(points):

        point = wgs84.latlon(lat, lon)
        satellite_passes = get_satellite_events(point, t0, t1, altitude_degrees=0.0)

        all_times = []
        all_bestSFs = []
        all_elevations = []

        for lap in satellite_passes:

            rise_time = lap[0]
            set_time = lap[2]

            elevation, times, ranges, doppler_shifts, doppler_rates = get_dopplereffect(point, rise_time, set_time)

            rcvd_powers = [received_power(range_) for range_ in ranges]
            bestSfs = [get_best_sf(shift, rate, P_r) for shift, rate, P_r in zip(doppler_shifts, doppler_rates, rcvd_powers)]

            all_times.append(times)
            all_bestSFs.append(bestSfs)
            all_elevations.append(elevation)

            plt.plot(times, bestSfs, color=_colors[i], label=f'ED={lat:.2f},{lon:.2f}')


    plt.title('Best LoRa SF per End-Device during satellite passes', fontsize=16)
    plt.xlabel('Time', fontsize=14)
    plt.ylabel('Elevation angle [degrees]', fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    #plt.legend(fontsize=10)
    plt.grid()
    plt.show()
