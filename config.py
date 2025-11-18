"""
Sensor configuration file.
Enable/disable sensors and configure their parameters here.
"""

# Load Cell Configuration
# Format: 'name': {
#     'enabled': bool,
#     'sig_plus_idx': int,
#     'sig_minus_idx': int,
#     'excitation_voltage': float,
#     'sensitivity': float
# }
LOAD_CELLS = {
    'LS1': {
        'enabled': True,
        'sig_plus_idx': 1,      # LS1_SIG+
        'sig_minus_idx': 0,     # LS1_SIG-
        'excitation_voltage': 5.0,
        'sensitivity': 0.020
    },
    'LS2': {
        'enabled': True,
        'sig_plus_idx': 7,      # LS2_SIG+
        'sig_minus_idx': 6,     # LS2_SIG-
        'excitation_voltage': 5.0,
        'sensitivity': 0.020
    },
    'LS3': {
        'enabled': True,
        'sig_plus_idx': 5,      # LS3_SIG+
        'sig_minus_idx': 4,     # LS3_SIG-
        'excitation_voltage': 5.0,
        'sensitivity': 0.020
    }
}

# Pressure Transducer Configuration
# Format: 'name': {
#     'enabled': bool,
#     'sig_idx': int,
#     'excitation_voltage': float,
#     'V_max': float,
#     'V_min': float,
#     'V_span': float,
#     'P_min': float,
#     'P_max': float
# }
PRESSURE_TRANSDUCERS = {
    'PT1': {
        'enabled': True,
        'sig_idx': 8,           # PT1_SIG
        'excitation_voltage': 5.0,
        'V_max': 4.5,
        'V_min': 0.5,
        'V_span': 4.0,
        'P_min': 0.0,
        'P_max': 100.0
    },
    'PT2': {
        'enabled': True,
        'sig_idx': 9,           # PT2_SIG (listed as PT1_SIG in CSV but appears to be PT2)
        'excitation_voltage': 5.0,
        'V_max': 4.5,
        'V_min': 0.5,
        'V_span': 4.0,
        'P_min': 0.0,
        'P_max': 100.0
    },
    'PT3': {
        'enabled': True,
        'sig_idx': 15,          # PT3_SIG
        'excitation_voltage': 5.0,
        'V_max': 4.5,
        'V_min': 0.5,
        'V_span': 4.0,
        'P_min': 0.0,
        'P_max': 100.0
    },
    'PT4': {
        'enabled': True,
        'sig_idx': 14,          # PT4_SIG
        'excitation_voltage': 5.0,
        'V_max': 4.5,
        'V_min': 0.5,
        'V_span': 4.0,
        'P_min': 0.0,
        'P_max': 100.0
    },
    'PT5': {
        'enabled': True,
        'sig_idx': 13,          # PT5_SIG
        'excitation_voltage': 5.0,
        'V_max': 4.5,
        'V_min': 0.5,
        'V_span': 4.0,
        'P_min': 0.0,
        'P_max': 100.0
    },
    'PT6': {
        'enabled': True,
        'sig_idx': 12,          # PT6_SIG
        'excitation_voltage': 5.0,
        'V_max': 4.5,
        'V_min': 0.5,
        'V_span': 4.0,
        'P_min': 0.0,
        'P_max': 100.0
    }
}

# RTD Configuration
# Format: 'name': {
#     'enabled': bool,
#     'V_leg1_idx': int,
#     'V_leg2_idx': int
# }
RTDS = {
    'RTD1': {
        'enabled': True,
        'V_leg1_idx': 3,        # RTD1_L1
        'V_leg2_idx': 2        # RTD1_L2
    },
    'RTD2': {
        'enabled': True,
        'V_leg1_idx': 11,       # RTD2_L1
        'V_leg2_idx': 10        # RTD2_L2
    }
}

