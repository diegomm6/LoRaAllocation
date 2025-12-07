import matplotlib.pyplot as plt
import numpy as np

# Data
years = np.arange(2013, 2026)
mioty_counts = [1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 4]
lr_counts = [0, 0, 0, 0, 0, 0, 0, 0, 1, 3, 5, 10, 18]

fig, ax = plt.subplots(figsize=(5, 4))

# Stacked bars
bars1 = ax.bar(years, mioty_counts, label='mioty', color='#f28e2b', width=0.75)
bars2 = ax.bar(years, lr_counts, bottom=mioty_counts, label='LR-FHSS', color='#4e79a7', width=0.75)

# Formatting
ax.set_title("LR-FHSS and mioty papers per year")
ax.set_xlabel("Year")
ax.set_ylabel("Number of papers")
ax.set_xticks(years[::2])  # Every 2 years
ax.set_ylim(0, max(np.array(mioty_counts) + np.array(lr_counts)) * 1.15)
ax.grid(axis='y', linestyle='--', alpha=0.3)
ax.legend()

# Add value labels
for i, (m, l) in enumerate(zip(mioty_counts, lr_counts)):
    if m > 0:
        ax.text(years[i], m/2, str(m), ha='center', va='center', 
                color='white', fontweight='bold', fontsize=10)
    if l > 0:
        ax.text(years[i], mioty_counts[i] + l/2, str(l), ha='center', va='center', 
                color='white', fontweight='bold', fontsize=10)

plt.tight_layout()
plt.savefig("lrfhss_mioty_papers_per_year.pdf", dpi=300, bbox_inches='tight')
#plt.show()

schedules = [[0, 4, 10, 1], [1, 5, 15, 1], [2, 5, 20, 1], [3, 6, 25, 1], [4, 6, 30, 1], [5, 6, 35, 1]]

schedules = np.array(schedules)
m_values = schedules[:, 1].astype(int)
tx_per_sf = np.bincount(m_values, minlength=6)
print("Transmissions per SF (index 0 = SF7):", tx_per_sf)
print(tx_per_sf[5])