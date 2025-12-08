import numpy as np
import matplotlib.pyplot as plt

# Data
num_devices = np.array([5, 28, 52, 76, 100])
timeslots = [91, 182, 455]
channels = ['2ch', '3ch']

markers = {'Opt1D': 'o', 'Opt2D': 's'}  # Markers for methods
linestyles = ['-', '--', '-.']           # Linestyles for channels (2ch, 3ch 91ts, 3ch 182ts/455ts)
colors = ['blue', 'orange', 'red']       # Colors for timeslots (91, 182, 455)


# Organized data: times[channels_idx][method_idx][timeslot_idx]
times = {
    '2ch': {
        'Opt1D': [np.array([0.056, 0.292, 0.561, 0.842, 1.412]),
                  np.array([0.105, 0.595, 1.243, 2.010, 2.712]),
                  np.array([0.435, 1.986, 3.957, 5.290, 6.893])],
        'Opt2D': [np.array([1.853, 12.633, 25.525, 44.362, 60.808]),
                  np.array([3.822, 27.203, 64.057, 91.280, 116.131]),
                  np.array([15.430, 89.958, 174.128, 243.477, 294.661])]
    },
    '3ch': {
        'Opt1D': [np.array([0.081, 0.417, 1.068, 1.447, 1.566]),
                  np.array([0.185, 1.020, 2.539, 3.058, 3.912]),
                  np.array([0.448, 2.312, 4.953, 8.241, 10.172])],
        'Opt2D': [np.array([2.868, 25.648, 47.543, 71.843, 94.340]),
                  np.array([7.494, 53.415, 101.306, 150.563, 177.036]),
                  np.array([18.256, 127.895, 280.781, 386.574, 498.893])]
    }
}

plt.figure(figsize=(8, 6))

for ch_idx, ch_name in enumerate(channels):
    for ts_idx, n_slots in enumerate(timeslots):
        color = colors[ts_idx]
        linestyle = linestyles[ch_idx]
        marker = markers['Opt1D']
        
        # Opt1D 
        plt.plot(num_devices, times[ch_name]['Opt1D'][ts_idx], 
                color=color, linestyle=linestyle, linewidth=3,
                marker=marker, markersize=8, markeredgewidth=2,
                alpha=0.9, label=f'Opt1D {ch_name} ({n_slots}ts)')

for ch_idx, ch_name in enumerate(channels):
    for ts_idx, n_slots in enumerate(timeslots):
        color = colors[ts_idx]
        linestyle = linestyles[ch_idx]
        marker = markers['Opt2D']
        
        # Opt2D
        plt.plot(num_devices, times[ch_name]['Opt2D'][ts_idx], 
                color=color, linestyle=linestyle, linewidth=3,
                marker=marker, markersize=8, markeredgewidth=2,
                alpha=0.9, label=f'Opt2D {ch_name} ({n_slots}ts)')


plt.title('Computation Time: Opt1D versus Opt2D', fontsize=18)
plt.xlabel('Number of Devices', fontsize=16)
plt.ylabel('Computation Time (s)', fontsize=16)
plt.yscale('log')
plt.xticks(num_devices, fontsize=14)
plt.yticks(fontsize=14)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=11)
plt.grid(True)

plt.savefig('img/computation_time_comparison.pdf')
#plt.show()
