import math

def calculate_lora_transmission_energy(payload_bytes, SF, tx_power_mw, 
                                       BW=125000, CR=1, preamble_length=8,
                                       header_enabled=True, crc_enabled=True):
    """
    Calculate LoRa transmission energy consumption.
    
    Parameters:
    -----------
    payload_bytes : int
        Number of bytes to transmit (X bytes)
    SF : int
        Spreading Factor (m) - range 7 to 12
    tx_power_mw : float
        Transmission power in milliwatts
    BW : int
        Bandwidth in Hz (default 125000 = 125 kHz)
    CR : int
        Coding Rate: 1=4/5, 2=4/6, 3=4/7, 4=4/8
    preamble_length : int
        Number of preamble symbols (typically 8)
    header_enabled : bool
        Explicit header enabled (True) or implicit (False)
    crc_enabled : bool
        CRC enabled
    
    Returns:
    --------
    dict : ToA (seconds, ms), Energy (Joules, mJ)
    """
    
    # Step 1: Calculate symbol duration
    Ts = (2 ** SF) / BW
    
    # Step 2: Determine Low Data Rate Optimization
    # Auto-enabled when symbol duration > 16ms (typically SF11-12 at BW=125kHz)
    low_data_rate_optimize = (Ts > 0.016)
    
    DE = 1 if low_data_rate_optimize else 0
    IH = 0 if header_enabled else 1
    CRC = 1 if crc_enabled else 0
    
    # Step 3: Calculate preamble duration
    T_preamble = (preamble_length + 4.25) * Ts
    
    # Step 4: Calculate number of payload symbols
    payload_symbols = 8 + max(
        math.ceil(
            (8 * payload_bytes - 4 * SF + 28 + 16 * CRC - 20 * IH) / 
            (4 * (SF - 2 * DE))
        ) * (CR + 4), 
        0
    )
    
    # Step 5: Calculate payload duration
    T_payload = payload_symbols * Ts
    
    # Step 6: Calculate total Time on Air
    ToA = T_preamble + T_payload
    
    # Step 7: Calculate energy consumption
    # E = P × t (convert mW to W)
    tx_power_watts = tx_power_mw / 1000.0
    energy_joules = tx_power_watts * ToA
    energy_mj = energy_joules * 1000
    
    return {
        'ToA_seconds': ToA,
        'ToA_ms': ToA * 1000,
        'Energy_joules': energy_joules,
        'Energy_mJ': energy_mj,
        'Power_mW': tx_power_mw
    }


# Example Usage
if __name__ == "__main__":

    SF = 12
    payload_bytes = 20

    result = calculate_lora_transmission_energy(
        payload_bytes=payload_bytes,   # X bytes
        SF=SF,              # m (spreading factor)
        tx_power_mw=389.4   # Based on LR1110 at 14 dBm
    )
    
    print(f"Payload: {payload_bytes} bytes")
    print(f"Spreading Factor: SF{SF}")
    print(f"Transmission Power: 389.4 mW")
    print(f"Time on Air: {result['ToA_ms']:.2f} ms")
    print(f"Energy Consumption: {result['Energy_mJ']:.2f} mJ")
    print(f"Energy Consumption: {result['Energy_joules']:.6f} J")
