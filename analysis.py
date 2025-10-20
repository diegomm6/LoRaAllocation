import numpy as np
import matplotlib.pyplot as plt

# New dataset (updated)
generated_packets = np.array([10.0, 167.0, 324.0, 482.0, 639.0, 796.0, 954.0, 1111.0,
                              1268.0, 1426.0, 1583.0, 1741.0, 1898.0, 2055.0, 2213.0,
                              2370.0, 2527.0, 2685.0, 2842.0, 3000.0])

# LRFHSS RX for CR1/3 and CR2/3
lrfhss_CR13_RX = np.array([200.0, 3314.5, 6319.0, 9159.5, 11726.5, 14092.0, 16012.0, 17691.5,
                            18947.5, 20103.0, 20791.5, 21398.0, 21717.0, 21679.5, 21702.0,
                            21337.5, 20839.0, 20150.0, 19576.0, 18751.0]) /20
lrfhss_CR23_RX = np.array([199.5, 3312.5, 6312.0, 9209.0, 11810.0, 14155.0, 16264.5, 17893.5,
                            19164.5, 20365.5, 20880.0, 21466.0, 21526.5, 21444.5, 21061.5,
                            20688.5, 19901.0, 19203.0, 18436.5, 17770.5]) /20


# LRFHSS RX interpolation function
def estimate_fhss_RX(sent_lrfhss, pure_lrfhss):
    estimated_rx = np.interp(sent_lrfhss, generated_packets, pure_lrfhss)
    return np.minimum(estimated_rx, sent_lrfhss)


# Methods data
opt1D_TX = np.array([10., 136., 136., 136., 136., 136., 136., 136., 136., 136.,
                     136., 136., 136., 136., 136., 136., 136., 136., 136., 136.])
opt1D_RX = opt1D_TX.copy()

classA_TX = np.array([4.675, 81.4, 163.45, 244.925, 318.35, 400.95, 478.975, 552.675,
                      631.8, 715.825, 789.425, 871.225, 951.675, 1029.8, 1109.55,
                      1183.925, 1267.35, 1344.6, 1429.75, 1503.5])
classA_RX = np.array([4.3, 28.675, 24., 16.025, 11.6, 7.325, 4.175, 2.8, 1.525, 1.05,
                      0.4, 0.4, 0.2, 0.025, 0.025, 0.075, 0., 0.025, 0., 0.025])

classA_validSF_TX = np.array([4.85, 83., 162.95, 240.75, 318.45, 396.85, 474.975,
                              557.575, 635.125, 714.775, 790.55, 869.325, 943.825,
                              1022.725, 1101.375, 1183.175, 1262.975, 1339.95,
                              1417.45, 1503.95])
classA_validSF_RX = np.array([4.6, 31.675, 23.3, 15.875, 12.225, 6.6, 5.3, 3.55, 3.025,
                              1.875, 1.975, 1.45, 1.125, 0.725, 0.95, 0.625, 0.575,
                              0.525, 0.45, 0.25])

success_best_TX = np.array([10., 50.5, 48.925, 49.9, 51.35, 48.8, 49.2, 47.925, 50.55,
                            51.55, 49.925, 50.075, 48.075, 51.475, 51.025, 50.925,
                            47.3, 50.475, 48.225, 48.75])
success_best_RX = np.array([9.125, 22.05, 22.925, 23., 22.325, 22.15, 22.925, 22.2,
                            22.525, 22.8, 20.875, 21.175, 21.9, 22.275, 22.875,
                            22.3, 21.275, 21.8, 21.225, 23.025])

success_seq_TX = np.array([10., 61.325, 62.625, 64.8, 65.575, 65., 64.225, 65.575,
                           64.15, 65.925, 65.675, 67.6, 64.25, 67.625, 64.375,
                           69.05, 67.45, 68.075, 66.525, 65.775])
success_seq_RX = np.array([8.775, 28.975, 28.35, 29.5, 28.45, 28.925, 29., 29.2, 28.2,
                           27.3, 27.325, 28.9, 28.925, 29.65, 29.3, 28.225, 29.125,
                           29.825, 28.9, 29.475])

max_tput_TX = np.array([10., 53.25, 57.075, 56.725, 56.075, 57.275, 56.5, 55.825,
                        57.35, 55.7, 59.35, 55.3, 57.8, 59.675, 58.825, 58.5,
                        58.25, 58.05, 58.125, 59.525])
max_tput_RX = np.array([8.4, 26.925, 27.7, 28.175, 27.1, 29.55, 27.5, 27.225, 26.3,
                        26.5, 27.325, 27.575, 27.575, 26.9, 27.625, 27.7, 28.675,
                        27.775, 26.75, 28.15])

max_tput_int_TX = np.array([10., 54.95, 56.45, 55.05, 58.35, 55.45, 57.95, 56.875,
                            62.075, 57.975, 57.9, 58.825, 57.625, 59.475, 58.675,
                            56.4, 58.65, 59.175, 58.6, 59.025])
max_tput_int_RX = np.array([8.425, 27.675, 28.475, 26.35, 27.825, 27.15, 27.675,
                            27.05, 26.85, 27.85, 27.5, 27.725, 27.475, 27.075,
                            27.75, 26.75, 28., 27.6, 27.45, 27.025])

# Compute combined RX and relative metrics
methods = {
    "opt1D": (opt1D_TX, opt1D_RX),
    "classA": (classA_TX, classA_RX),
    "classA_validSF": (classA_validSF_TX, classA_validSF_RX),
    "success_best": (success_best_TX, success_best_RX),
    "success_seq": (success_seq_TX, success_seq_RX),
    "max_tput": (max_tput_TX, max_tput_RX),
    "max_tput_int": (max_tput_int_TX, max_tput_int_RX)
}

results = {}
for name, (tx, rx) in methods.items():
    lrfhss_tx = generated_packets - tx
    lrfhss_rx_cr13 = estimate_fhss_RX(lrfhss_tx, lrfhss_CR13_RX)
    lrfhss_rx_cr23 = estimate_fhss_RX(lrfhss_tx, lrfhss_CR23_RX)

    total_rx_cr13 = rx + lrfhss_rx_cr13
    total_rx_cr23 = rx + lrfhss_rx_cr23

    wasted_cr13 = generated_packets - total_rx_cr13
    wasted_cr23 = generated_packets - total_rx_cr23

    pdr_cr13 = total_rx_cr13 / generated_packets
    pdr_cr23 = total_rx_cr23 / generated_packets

    results[name] = {"total_rx_cr13": total_rx_cr13, "total_rx_cr23": total_rx_cr23, 
                    "wasted_cr13": wasted_cr13, "wasted_cr23": wasted_cr23,
                    "pdr_cr13": pdr_cr13, "pdr_cr23": pdr_cr23,}


# Add PDR for pure LRFHSS
pure_lrfhss_pdr_cr13 = lrfhss_CR13_RX / generated_packets
pure_lrfhss_pdr_cr23 = lrfhss_CR23_RX / generated_packets

for name in results:
    results[name]['relative_throughput_cr13'] = results[name]['total_rx_cr13'] / lrfhss_CR13_RX
    results[name]['relative_pdr_cr13'] = results[name]['pdr_cr13'] / lrfhss_CR13_RX
    results[name]['relative_throughput_cr23'] = results[name]['total_rx_cr23'] / lrfhss_CR23_RX
    results[name]['relative_pdr_cr23'] = results[name]['pdr_cr23'] / lrfhss_CR23_RX






# Plot: Absolute Throughput (Total Received Packets) for All Methods
plt.figure(figsize=(10, 6))

# Plot pure LRFHSS CR1/3 and CR2/3 throughput
plt.plot(generated_packets, lrfhss_CR13_RX, 'k-o', label='LRFHSS CR1/3 Throughput')
plt.plot(generated_packets, lrfhss_CR23_RX, 'k--o', label='LRFHSS CR2/3 Throughput')

# Plot joint methods throughput
for name, vals in results.items():
    plt.plot(generated_packets, vals["total_rx_cr13"], marker='o', label=f'{name} Throughput')

plt.xlabel("Total Generated Packets")
plt.ylabel("Absolute Throughput (Received Packets)")
plt.title("Absolute Throughput vs Total Generated Packets")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()


# Plot: Absolute PDR comparing LRFHSS CR1/3 and CR2/3 plus joint methods
plt.figure(figsize=(10, 6))
plt.plot(generated_packets, pure_lrfhss_pdr_cr13, 'k-o', label='LRFHSS CR1/3 PDR')
plt.plot(generated_packets, pure_lrfhss_pdr_cr23, 'k--o', label='LRFHSS CR2/3 PDR')
for name, vals in results.items():
    plt.plot(generated_packets, vals["pdr_cr13"], marker='o', label=f'{name} PDR')
plt.xlabel("Total Generated Packets")
plt.ylabel("Packet Delivery Ratio (PDR)")
plt.title("Absolute Packet Delivery Ratio vs Total Generated Packets")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()



# Plot: Relative Throughput to LRFHSS CR1/3
plt.figure(figsize=(10, 6))
for name, vals in results.items():
    plt.plot(generated_packets, vals["relative_throughput_cr13"], marker='o', label=f'{name} Rel Throughput CR1/3')
plt.axhline(1.0, color='k', linestyle='--', label='LRFHSS CR1/3 Reference')
plt.xlabel("Total Generated Packets")
plt.ylabel("Relative Throughput (to LRFHSS CR1/3)")
plt.title("Relative Throughput vs Total Generated Packets (CR1/3 Reference)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# Plot: Relative Throughput to LRFHSS CR2/3
plt.figure(figsize=(10, 6))
for name, vals in results.items():
    plt.plot(generated_packets, vals["relative_throughput_cr23"], marker='o', label=f'{name} Rel Throughput CR2/3')
plt.axhline(1.0, color='k', linestyle='--', label='LRFHSS CR2/3 Reference')
plt.xlabel("Total Generated Packets")
plt.ylabel("Relative Throughput (to LRFHSS CR2/3)")
plt.title("Relative Throughput vs Total Generated Packets (CR2/3 Reference)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()


# Plot: Relative PDR to LRFHSS CR1/3
plt.figure(figsize=(10, 6))
for name, vals in results.items():
    plt.plot(generated_packets, vals["relative_pdr_cr13"], marker='o', label=f'{name} Rel PDR CR1/3')
plt.axhline(1.0, color='k', linestyle='--', label='LRFHSS CR1/3 Reference')
plt.xlabel("Total Generated Packets")
plt.ylabel("Relative PDR (to LRFHSS CR1/3)")
plt.title("Relative Packet Delivery Ratio vs Total Generated Packets (CR1/3 Reference)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# Plot: Relative PDR to LRFHSS CR2/3
plt.figure(figsize=(10, 6))
for name, vals in results.items():
    plt.plot(generated_packets, vals["relative_pdr_cr23"], marker='o', label=f'{name} Rel PDR CR2/3')
plt.axhline(1.0, color='k', linestyle='--', label='LRFHSS CR2/3 Reference')
plt.xlabel("Total Generated Packets")
plt.ylabel("Relative PDR (to LRFHSS CR2/3)")
plt.title("Relative Packet Delivery Ratio vs Total Generated Packets (CR2/3 Reference)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()


