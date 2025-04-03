import numpy as np
import matplotlib.pyplot as plt

from scipy.special import iv  # Modified Bessel function I0
from scipy.stats import rice, nakagami
from base import *


# Parameters
K = 4.0  # Rice factor (example for light shadowing)
mu = 0.13  # Mean of lognormal shadowing
sigma = 1.0  # Standard deviation of lognormal shadowing (dB spread)
num_samples = 1000  # Number of samples
r_values = np.linspace(0, 10, num_samples)  # Range of r values

# Lognormal shadowing parameters
h = np.log(10) / 20

def rice_pdf(r, S, K):
    """Rice PDF conditioned on shadowing factor S."""
    return (2 * (K + 1) * r / S**2) * np.exp(-(K + 1) * r**2 / S**2 - K) * iv(0, 2 * r / S * np.sqrt(K * (K + 1)))

def lognormal_pdf(S, mu, sigma):
    """Lognormal PDF for shadowing."""
    return (1 / (np.sqrt(2 * np.pi) * h * sigma * S)) * np.exp(-((np.log(S) - mu)**2 / (2 * (h * sigma)**2)))

def fading_channel_pdf(r_values, K, mu, sigma):
    """Combined fading channel PDF integrating over shadowing."""
    pdf_values = np.zeros_like(r_values)
    S_values = np.linspace(0.01, 10, num_samples)
    
    for i, r in enumerate(r_values):
        integrand = [rice_pdf(r, S, K) * lognormal_pdf(S, mu, sigma) for S in S_values]
        pdf_values[i] = np.trapz(integrand, S_values)
    
    return pdf_values

# Calculate the fading channel PDF
fading_pdf_values = fading_channel_pdf(r_values, K, mu, sigma)

# Plot the result
plt.plot(r_values, fading_pdf_values)
plt.title("Fading Channel PDF with Rice and Lognormal Shadowing")
plt.xlabel("Received Signal Envelope (r)")
plt.ylabel("Probability Density")
plt.grid(True)
plt.show()



nu = 3

# Coefficients for K-factor, mu, and sigma from Table I
K0, K1, K2 = 2.731, -1.0474e-1, 2.7740e-3
sigma0, sigma1 = 4.5, -0.05

def K(alpha):
    return K0 + K1 * alpha + K2 * alpha**2

def sigma(alpha):
    return sigma0 + sigma1 * alpha


# Function to calculate SNR
def calculate_snr(distance, alpha):
    path_loss = fspl_w(distance)
    
    # Sample a value from Rice fading distribution
    a = alpha * 180 / np.pi
    shape_param = np.sqrt(K(a))
    #h_fading = rice.rvs(shape_param, scale=sigma(a))
    h_fading = nakagami.rvs(nu)

    #h_fading = 1
    
    # Calculate SNR
    snr_linear = (dBm2mW(TX_POWER) * path_loss * h_fading**2) / dBm2mW(AWGN_VAR_DB)
    
    return snr_linear


Eangle = 60 * np.pi / 180
Range = dist2sat_angle(Eangle)

Eangles_deg = np.linspace(30, 80, 1000) 
Eangles_rad = Eangles_deg * np.pi / 180


def getSNR(angle):
    range_ = dist2sat_angle(angle)
    SNR = mW2dBm(calculate_snr(range_, angle))
    return SNR

avgSNR = 0
nSamples = 100
SNRvalues=[]

print(F"noise_power_dbm = {AWGN_VAR_DB} db")

for Ea in Eangles_rad:
    for i in range(nSamples):
        avgSNR += getSNR(Ea)
    SNRvalues.append(avgSNR / nSamples)
    avgSNR=0

plt.plot(Eangles_deg, SNRvalues)
plt.xlabel('Elevation angle')
plt.ylabel('SNR')
plt.title('SNR')
plt.show()
