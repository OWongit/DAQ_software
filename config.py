"""
Sensor configuration file.
Enable/disable sensors and configure their parameters here.
"""

# Load Cell Configuration
# Format: 'name': {
#     'enabled': bool,
#     'ADC': int,
#     'sig_plus_idx': int,
#     'sig_minus_idx': int,
#     'excitation_voltage': float,
#     'sensitivity': float
# }
LOAD_CELLS = {
    "LC1": {
        # DO NOT CHANGE VALUES ADC, SIG_PLUS_IDX, SIG_MINUS_IDX
        "enabled": True,
        "ADC": 1,
        "sig_plus_idx": 1,
        "sig_minus_idx": 0,
        "excitation_voltage": 10.0,
        "sensitivity": 0.020,
        "max_load": 907.1847,
    },
    "LC2": {
        # DO NOT CHANGE VALUES ADC, SIG_PLUS_IDX, SIG_MINUS_IDX
        "enabled": True,
        "ADC": 1,
        "sig_plus_idx": 7,
        "sig_minus_idx": 6,
        "excitation_voltage": 5.0,
        "sensitivity": 0.020,
        "max_load": 60.0,
    },
    "LC3": {
        # DO NOT CHANGE VALUES ADC, SIG_PLUS_IDX, SIG_MINUS_IDX
        "enabled": True,
        "ADC": 1,
        "sig_plus_idx": 5,
        "sig_minus_idx": 4,
        "excitation_voltage": 5.0,
        "sensitivity": 0.020,
        "max_load": 10.0,
    },
}

# Pressure Transducer Configuration
# Format: 'name': {
#     'enabled': bool,
#     'ADC': int,
#     'sig_idx': int,
#     'excitation_voltage': float,
#     'V_max': float,
#     'V_min': float,
#     'V_span': float,
#     'P_min': float,
#     'P_max': float
# }
PRESSURE_TRANSDUCERS = {
    "PT1": {
        # DO NOT CHANGE VALUES ADC, SIG_IDX
        "enabled": True,
        "ADC": 2,
        "sig_idx": 9,
        "excitation_voltage": 5.0,
        "V_max": 4.5,
        "V_min": 0.5,
        "V_span": 4.0,
        "P_min": 0.0,
        "P_max": 100.0,
    },
    "PT2": {
        # DO NOT CHANGE VALUES ADC, SIG_IDX
        "enabled": True,
        "ADC": 2,
        "sig_idx": 8,
        "excitation_voltage": 5.0,
        "V_max": 4.5,
        "V_min": 0.5,
        "V_span": 4.0,
        "P_min": 0.0,
        "P_max": 100.0,
    },
    "PT3": {
        # DO NOT CHANGE VALUES ADC, SIG_IDX
        "enabled": True,
        "ADC": 2,
        "sig_idx": 15,
        "excitation_voltage": 5.0,
        "V_max": 4.5,
        "V_min": 0.5,
        "V_span": 4.0,
        "P_min": 0.0,
        "P_max": 100.0,
    },
    "PT4": {
        # DO NOT CHANGE VALUES ADC, SIG_IDX
        "enabled": True,
        "ADC": 2,
        "sig_idx": 14,
        "excitation_voltage": 5.0,
        "V_max": 4.5,
        "V_min": 0.5,
        "V_span": 4.0,
        "P_min": 0.0,
        "P_max": 100.0,
    },
    "PT5": {
        # DO NOT CHANGE VALUES ADC, SIG_IDX
        "enabled": True,
        "ADC": 2,
        "sig_idx": 13,
        "excitation_voltage": 5.0,
        "V_max": 4.5,
        "V_min": 0.5,
        "V_span": 4.0,
        "P_min": 0.0,
        "P_max": 100.0,
    },
    "PT6": {
        # DO NOT CHANGE VALUES ADC, SIG_IDX
        "enabled": True,
        "ADC": 2,
        "sig_idx": 12,
        "excitation_voltage": 5.0,
        "V_max": 4.5,
        "V_min": 0.5,
        "V_span": 4.0,
        "P_min": 0.0,
        "P_max": 100.0,
    },
}

# RTD Configuration
# Format: 'name': {
#     'enabled': bool,
#     'ADC': int,
#     'V_lead1_idx': int,
#     'V_lead2_idx': int
# }
RTDS = {
    "RTD1": {"enabled": True, "ADC": 1, "V_lead1_idx": 3, "V_lead2_idx": 2},  # DO NOT CHANGE VALUES ADC, V_lead1_idx, V_lead2_idx
    "RTD2": {"enabled": True, "ADC": 2, "V_lead1_idx": 11, "V_lead2_idx": 10},  # DO NOT CHANGE VALUES ADC, V_lead1_idx, V_lead2_idx
}
