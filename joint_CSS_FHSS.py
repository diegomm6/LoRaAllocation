import numpy as np
import matplotlib.pyplot as plt
from src.base import COLORS3

simtime = 15
PL_BYTES = 20      # Typical LoRa payload bytes
LR1120_POW = 92.4  # mW at 14 dBm

# LRFHSS RX interpolation function
def estimate_fhss_RX(sent_lrfhss, pure_lrfhss):
    estimated_rx = np.interp(sent_lrfhss, generated_packets, pure_lrfhss)
    return np.minimum(estimated_rx, sent_lrfhss)

generated_packets = np.array([
    5.0, 39.0, 73.0, 107.0, 142.0, 176.0, 210.0, 245.0, 279.0, 313.0,
    348.0, 382.0, 416.0, 451.0, 485.0, 519.0, 553.0, 588.0, 622.0, 656.0,
    691.0, 725.0, 759.0, 794.0, 828.0, 862.0, 897.0, 931.0, 965.0, 1000.0
], dtype=float)


load = generated_packets / simtime


# LR-FHSS
lrfhss_RX = np.array([
   4.975,  38.7  ,  70.975, 101.525, 128.7  , 153.225, 172.075, 188.8  , 201.875, 214.325,
 220.575, 222.725, 225.825, 227.625, 225.35 , 215.25 , 213.425, 206.025, 197.85 , 188.5  ,
 178.15 , 166.325, 156.1  , 148.075, 138.75 , 127.35 , 119.425, 108.325, 101.9  ,  92.325
], dtype=float)

pure_lrfhss_pdr = lrfhss_RX / generated_packets

# opt1D
opt1D_TX = np.array([5., 39., 73., 107., 117., 123., 131., 142., 159., 164.,
                     171., 171., 171., 171., 171., 171., 171., 171., 171., 171.,
                     171., 171., 171., 171., 171., 171., 171., 171., 171., 171.])
opt1D_RX = np.array([4., 38., 72., 106., 116., 122., 130., 141., 158., 163.,
                     170., 170., 170., 170., 170., 170., 170., 170., 170., 170.,
                     170., 170., 170., 170., 171., 170., 171., 170., 170., 170.])

# class A
classA_TX = np.array([  2.4  ,  19.975,  35.45 ,  52.9  ,  71.55 ,  86.225, 105.925, 122.075,
                       141.275, 156.775, 175.8  , 192.2  , 206.85 , 225.825, 240.75 , 258.7  ,
                       277.5  , 293.65 , 308.725, 326.3  , 346.725, 359.35 , 379.325, 398.525,
                       414.625, 426.7  , 449.45 , 464.975, 480.7  , 498.525], dtype=float)

classA_RX = np.array([2.2  , 7.15 , 5.9  , 4.2  , 1.875, 1.425, 0.925, 0.35 , 0.4  , 0.25 ,
                      0.125, 0.075, 0.025, 0.025, 0.   , 0.   , 0.   , 0.   , 0.   , 0.   ,
                      0.   , 0.   , 0.   , 0.   , 0.   , 0.   , 0.   , 0.   , 0.   , 0.   ], dtype=float)

# class A valid SF
classA_validSF_TX = np.array([  2.675,  19.9  ,  36.85 ,  52.9  ,  71.775,  86.4  , 105.55 , 122.   ,
                               140.8  , 155.075, 173.825, 190.25 , 209.2  , 227.475, 242.2  , 258.65 ,
                               274.225, 292.25 , 311.   , 329.15 , 344.1  , 359.425, 384.375, 400.   ,
                               415.225, 430.85 , 448.95 , 467.425, 483.975, 496.475], dtype=float)

classA_validSF_RX = np.array([ 2.125, 10.125, 11.85 , 12.975, 14.9  , 14.425, 16.1  , 16.525, 19.275, 19.275,
                              21.925, 22.325, 24.45 , 27.225, 29.375, 28.7  , 29.05 , 30.675, 31.95 , 32.   ,
                              33.325, 33.275, 35.85 , 35.15 , 36.8  , 37.325, 36.9  , 38.5  , 39.475, 39.375], dtype=float)

# success-based best SF
success_best_TX = np.array([  5.   ,  39.   ,  73.   , 107.   , 111.475, 111.4  , 111.   , 110.425, 112.65 ,
                             111.5  , 111.575, 110.9  , 110.35 , 112.55 , 110.95 , 109.775, 111.6  , 112.425,
                             113.2  , 113.95 , 111.05 , 110.475, 113.975, 107.85 , 111.05 , 111.7  , 111.625,
                             111.875, 111.95 , 108.95 ], dtype=float)

success_best_RX = np.array([ 1.9  , 12.925, 16.925, 20.175, 20.475, 19.   , 20.05 , 18.775, 21.7  , 20.775,
                             21.45 , 22.25 , 21.3  , 22.125, 21.7  , 21.95 , 23.025, 23.45 , 23.075, 23.025,
                             21.725, 22.875, 23.3  , 22.575, 23.225, 22.6  , 21.875, 23.075, 22.975, 22.5  ], dtype=float)

# success-based sequential SF
success_seq_TX = np.array([  5.   ,  39.   ,  73.   , 107.   , 122.35 , 130.275, 135.85 , 140.575, 144.875,
                            145.55 , 150.5  , 145.05 , 149.55 , 153.075, 151.675, 152.525, 155.725, 155.65 ,
                            158.75 , 157.75 , 156.45 , 156.675, 157.95 , 160.3  , 156.625, 155.525, 160.7  ,
                            161.975, 161.225, 162.05 ], dtype=float)

success_seq_RX = np.array([ 1.925, 12.4  , 16.7  , 21.175, 28.075, 29.775, 32.75 , 33.1  , 35.4  , 35.25 ,
                            36.275, 34.875, 34.2  , 35.2  , 35.075, 35.4  , 34.825, 36.95 , 35.95 , 37.925,
                            35.4  , 35.675, 36.225, 37.525, 35.6  , 36.975, 37.375, 36.4  , 35.8  , 36.275], dtype=float)

# max-throughput conservative
max_tput_cons_TX = np.array([ 5.   , 39.   , 53.25 , 58.375, 58.875, 62.4  , 64.05 , 64.1  , 63.675, 66.925,
                              66.025, 63.2  , 64.825, 67.15 , 65.325, 65.425, 67.4  , 64.8  , 65.75 , 66.375,
                              65.925, 66.3  , 67.925, 66.4  , 66.025, 66.075, 67.925, 68.45 , 66.175, 66.95 ], dtype=float)

max_tput_cons_RX = np.array([ 1.9  , 12.95 , 17.325, 19.15 , 18.85 , 19.9  , 19.55 , 20.425, 21.1  , 21.075,
                              21.275, 21.175, 21.65 , 23.525, 23.9  , 22.275, 23.025, 22.45 , 22.675, 21.85 ,
                              22.6  , 23.525, 23.225, 22.1  , 21.975, 22.925, 23.825, 23.1  , 23.075, 23.3  ], dtype=float)

# max-throughput interference
max_tput_int_TX = np.array([ 5.   , 39.   , 53.4  , 57.575, 60.875, 62.7  , 63.5  , 63.05 , 63.95 , 64.85 ,
                             66.075, 66.2  , 64.95 , 64.975, 67.725, 67.   , 66.35 , 65.425, 67.55 , 67.375,
                             67.025, 68.4  , 65.1  , 69.05 , 67.1  , 65.5  , 68.35 , 67.125, 66.775, 70.075], dtype=float)

max_tput_int_RX = np.array([ 1.975, 12.825, 17.225, 19.075, 18.75 , 19.925, 20.1  , 21.475, 21.025, 21.   ,
                              21.075, 21.575, 20.8  , 21.05 , 23.575, 23.3  , 22.3  , 21.9  , 23.825, 23.15 ,
                              23.05 , 22.7  , 22.1  , 22.6  , 23.7  , 22.05 , 21.675, 22.65 , 23.6  , 25.1  ], dtype=float)


####################################################################################################
####################################################################################################


labels1 = [
    "Opt1D",
    "Joint ClassA",
    "Joint ClassA Valid-SF",
    "Success Best-SF",
    "Success Seq-SF",
    "ALOHA Best-SF",
    "ALOHA Seq-SF",
]

label_to_arrays = {
    "Opt1D": (opt1D_TX, opt1D_RX),
    "Joint ClassA": (classA_TX, classA_RX),
    "Joint ClassA Valid-SF": (classA_validSF_TX, classA_validSF_RX),
    "Success Best-SF": (success_best_TX, success_best_RX),
    "Success Seq-SF": (success_seq_TX, success_seq_RX),
    "ALOHA Best-SF": (max_tput_cons_TX, max_tput_cons_RX),
    "ALOHA Seq-SF": (max_tput_int_TX, max_tput_int_RX),
}

# Compute combined RX and metrics using the chosen LR-FHSS curve (lrfhss_RX)
results = {}
for label in labels1:
    tx, rx = label_to_arrays[label]
    lrfhss_tx = generated_packets - tx
    lrfhss_rx = estimate_fhss_RX(lrfhss_tx, lrfhss_RX)

    total_rx = rx + lrfhss_rx
    wasted = generated_packets - total_rx
    pdr = total_rx / generated_packets

    results[label] = {"total_rx": total_rx, "wasted": wasted, "pdr": pdr}

# Build the pure LR-FHSS references for relative plots
pure_lrfhss_pdr = lrfhss_RX / generated_packets

# Relative metrics (throughput relative to LR-FHSS throughput, PDR relative to LR-FHSS PDR)
for label in labels1:
    results[label]["relative_throughput"] = results[label]["total_rx"] / lrfhss_RX
    results[label]["relative_pdr"] = results[label]["pdr"] / pure_lrfhss_pdr


####################################################################################################
####################################################################################################

# ---------------------------
# Plot: Absolute Throughput
# ---------------------------
plt.figure(figsize=(10, 8))
plt.plot(load, lrfhss_RX, 'k-o', label='pure LR-FHSS Throughput')
for i, label in enumerate(labels1):
    plt.plot(load, results[label]["total_rx"], marker='o', color=COLORS3[i], label=f'{label}')

plt.title("Absolute Throughput vs Traffic Load", fontsize=22)
plt.xlabel("Load (packets/s)", fontsize=20)
plt.ylabel("Absolute Throughput (Received Packets)", fontsize=20)
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)
plt.legend(fontsize=15)
plt.grid(True)
# plt.show()
plt.savefig('img/absolute_throughput.pdf')
plt.close()

# ---------------------------
# Plot: Absolute PDR
# ---------------------------
plt.figure(figsize=(10, 8))
plt.plot(load, pure_lrfhss_pdr, 'k-o', label='Pure LR-FHSS')
for i, label in enumerate(labels1):
    plt.plot(load, results[label]["pdr"], marker='o', color=COLORS3[i], label=f'{label}')

plt.title("Absolute Packet Delivery Ratio PDR vs Traffic Load", fontsize=22)
plt.xlabel("Load (packets/s)", fontsize=20)
plt.ylabel("PDR", fontsize=20)
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)
plt.legend(fontsize=14)
plt.grid(True)
# plt.show()
plt.savefig('img/absolute_pdr.pdf')
plt.close()

# ---------------------------
# Plot: Relative Throughput to LR-FHSS
# ---------------------------
plt.figure(figsize=(10, 8))
for i, label in enumerate(labels1):
    plt.plot(load, results[label]["relative_throughput"], marker='o', color=COLORS3[i], label=f'{label}')
plt.axhline(1.0, color='k', linestyle='--', label='Pure LR-FHSS Ref.')

plt.title("Relative Throughput vs Traffic Load", fontsize=22)
plt.xlabel("Load (packets/s)", fontsize=20)
plt.ylabel("Relative Throughput", fontsize=20)
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)
plt.legend(fontsize=14)
plt.grid(True)
# plt.show()
plt.savefig('img/relativeFHSS_throughput.pdf')
plt.close()

# ---------------------------
# Plot: Relative PDR to LR-FHSS
# ---------------------------
plt.figure(figsize=(10, 8))
for i, label in enumerate(labels1):
    plt.plot(load, results[label]["relative_pdr"], marker='o', color=COLORS3[i], label=f'{label}')
plt.axhline(1.0, color='k', linestyle='--', label='Pure LR-FHSS Ref.')

plt.title("Relative Packet Delivery Ratio vs Traffic Load", fontsize=22)
plt.xlabel("Load (packets/s)", fontsize=20)
plt.ylabel("Relative PDR", fontsize=20)
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)
plt.legend(fontsize=14)
plt.grid(True)
# plt.show()
plt.savefig('img/relativeFHSS_pdr.pdf')
plt.close()
