import numpy as np

def get_energy_consumption(num_header, num_fragments, tx_power_dbm=14, supply_voltage=3.3):
    """
    Calculate energy consumption for an LR-FHSS packet based on the paper:
    "Experiment-based Models for Air Time and Current Consumption of LoRaWAN LR-FHSS"
    
    Parameters:
    -----------
    num_header : int
        Number of header replicas (NH). Typically 2 for DR9/DR11 or 3 for DR8/DR10
    num_fragments : int
        Number of payload fragments (NF)
    tx_power_dbm : float
        Transmit power in dBm (default: 14 dBm). Range: 0-22 dBm
    supply_voltage : float
        Supply voltage in volts (default: 3.3V)
    
    Returns:
    --------
    dict : Dictionary containing:
        - 'energy_mJ': Total energy consumption in millijoules
        - 'time_on_air_ms': Time on air in milliseconds
        - 'avg_current_mA': Average current consumption in milliamperes
        - 'tx_current_mA': Transmit mode current in milliamperes
        - 'breakdown': Dictionary with energy breakdown by state
    """
    
    # Constants from Table IV of the paper
    # State durations (ms)
    T_wu = 0.4301      # Wake up
    T_pre = 99.67      # Radio preparation
    T_off = 9.45       # Radio off
    T_std_final = 1.044  # Final standby
    TT = 0.61          # Transition time between hops
    
    # Current consumption (mA) - independent of transmit power
    I_wu = 1.9000      # Wake up
    I_std = 1.2303     # Standby
    I_fs = 3.7721      # Frequency synthesis
    I_pre = 2.9781     # Radio preparation
    I_off = 4.8880     # Radio off
    I_sleep = 0.0684   # Sleep
    
    # LR-FHSS parameters
    Rb = 488.28125     # Instantaneous bit rate (bps)
    Hb = 114           # Encoded header bits
    Fb = 50            # Encoded fragment bits (48 payload + 2 preamble)
    
    # Transmit mode current consumption as function of power (from Fig. 7 and Fig. 13)
    # Empirical model based on measurements
    if tx_power_dbm <= 14:
        # Low Power Amplifier (LPA) region - approximately linear
        I_tx = 24.5 + (tx_power_dbm - 0) * (27.5 - 24.5) / 14
    else:
        # High Power Amplifier (HPA) region - steeper increase
        I_tx = 27.5 + (tx_power_dbm - 14) * (54.0 - 27.5) / 8
    
    # Calculate standby and frequency synthesis durations
    # These depend on payload (from Fig. 9)
    # Approximation based on the figure
    T_std_initial = 25 + num_fragments * 0.5  # ms (approximation)
    T_fs = 52 + num_fragments * 0.3           # ms (approximation)
    
    # Calculate Time on Air (ToA) - Equation (4) from the paper
    # T_tx = (PB / Rb) + (TT * NT)
    # where PB = Hb*NH + PL (total encoded bits)
    # NT = NH + NF - 1 (number of transitions)
    
    PB = Hb * num_header + Fb * num_fragments  # Total encoded bits
    NT = num_header + num_fragments - 1         # Number of transitions
    
    # Convert to milliseconds
    T_tx = (PB / Rb) * 1000 + TT * NT  # Time on air in ms
    
    # Calculate average current during transition (Equation 12)
    I_T = (I_tx + I_off + I_tx) / 3
    
    # Calculate current drop during transitions (Equation 11)
    I_D = I_tx - I_T
    
    # Calculate total active time (Equation 14)
    T_active = T_wu + T_std_initial + T_fs + T_pre + T_tx + T_off + T_std_final
    
    # Calculate energy for each state (E = V * I * t)
    # Energy in millijoules (mJ)
    E_wu = supply_voltage * I_wu * T_wu / 1000
    E_std_initial = supply_voltage * I_std * T_std_initial / 1000
    E_fs = supply_voltage * I_fs * T_fs / 1000
    E_pre = supply_voltage * I_pre * T_pre / 1000
    E_tx = supply_voltage * I_tx * T_tx / 1000
    E_transition = supply_voltage * I_D * TT * NT / 1000  # Energy saved during transitions
    E_off = supply_voltage * I_off * T_off / 1000
    E_std_final = supply_voltage * I_std * T_std_final / 1000
    
    # Total energy (accounting for transition drops)
    E_total = E_wu + E_std_initial + E_fs + E_pre + E_tx - E_transition + E_off + E_std_final
    
    # Calculate average current (Equation 10 simplified for single transmission)
    # Sum of (T_i * I_i) for all states, accounting for transitions
    current_time_product = (
        T_wu * I_wu +
        T_std_initial * I_std +
        T_fs * I_fs +
        T_pre * I_pre +
        T_tx * I_tx +
        T_off * I_off +
        T_std_final * I_std -
        TT * I_D * NT
    )
    I_avg = current_time_product / T_active
    
    # Return results
    return {
        'energy_mJ': E_total,
        'time_on_air_ms': T_tx,
        'avg_current_mA': I_avg,
        'tx_current_mA': I_tx,
        'total_active_time_ms': T_active,
        'breakdown': {
            'wake_up_mJ': E_wu,
            'standby_initial_mJ': E_std_initial,
            'frequency_synthesis_mJ': E_fs,
            'radio_prep_mJ': E_pre,
            'transmit_mJ': E_tx,
            'transition_savings_mJ': E_transition,
            'radio_off_mJ': E_off,
            'standby_final_mJ': E_std_final
        }
    }


def calculate_fragments(payload_bytes, code_rate):
    """
    Calculate the number of fragments (NF) for a given payload size
    
    Parameters:
    -----------
    payload_bytes : int
        Payload size in bytes (L)
    code_rate : str
        Code rate: '1/3' for DR8/DR10 or '2/3' for DR9/DR11
    
    Returns:
    --------
    int : Number of payload fragments (NF)
    """
    P_CRC = 2  # CRC bytes
    OB = 6     # Overhead bits
    
    # Convert code rate string to fraction
    if code_rate == '1/3':
        CR = 1/3
    elif code_rate == '2/3':
        CR = 2/3
    else:
        raise ValueError("Code rate must be '1/3' or '2/3'")
    
    # Calculate encoded payload bits (Equation 7)
    P_L = np.ceil((8 * payload_bytes + P_CRC) / CR + OB)
    
    # Calculate number of fragments (Equation 8)
    # Each fragment holds 48 bits
    NF = int(np.ceil(P_L / 48))
    
    return NF


def get_energy_from_payload(payload_bytes, data_rate='DR8', tx_power_dbm=14, supply_voltage=3.3):
    """
    Calculate energy consumption from payload size and data rate
    
    Parameters:
    -----------
    payload_bytes : int
        Payload size in bytes
    data_rate : str
        'DR8' or 'DR10' (NH=3, CR=1/3) or 'DR9' or 'DR11' (NH=2, CR=2/3)
    tx_power_dbm : float
        Transmit power in dBm (default: 14 dBm)
    supply_voltage : float
        Supply voltage in volts (default: 3.3V)
    
    Returns:
    --------
    dict : Energy consumption results
    """
    # Determine header replicas and code rate based on DR
    if data_rate in ['DR8', 'DR10']:
        num_header = 3
        code_rate = '1/3'
    elif data_rate in ['DR9', 'DR11']:
        num_header = 2
        code_rate = '2/3'
    else:
        raise ValueError("data_rate must be 'DR8', 'DR9', 'DR10', or 'DR11'")
    
    # Calculate number of fragments
    num_fragments = calculate_fragments(payload_bytes, code_rate)
    
    # Calculate energy
    result = get_energy_consumption(num_header, num_fragments, tx_power_dbm, supply_voltage)
    result['payload_bytes'] = payload_bytes
    result['data_rate'] = data_rate
    result['num_fragments'] = num_fragments
    result['num_headers'] = num_header
    
    return result


# Example usage
if __name__ == "__main__":
    # Example 1: Direct usage with header and fragment counts
    result = get_energy_consumption(num_header=3, num_fragments=9, tx_power_dbm=14)
    print(f"Energy: {result['energy_mJ']:.2f} mJ")
    print(f"Time on Air: {result['time_on_air_ms']:.2f} ms")
    print(f"Average Current: {result['avg_current_mA']:.2f} mA")
    
    # Example 2: Usage with payload size and data rate
    result = get_energy_from_payload(payload_bytes=20, data_rate='DR9', tx_power_dbm=14)
    print(f"\nFor 20-byte payload on DR8:")
    print(f"Energy: {result['energy_mJ']:.2f} mJ")
    print(f"Time on Air: {result['time_on_air_ms']:.2f} ms")
    print(f"headers used: {result['num_headers']}, fragments used: {result['num_fragments']}")
