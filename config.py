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
        'sig_plus_idx': 1,      # LS1_SIG+ DO NOT CHANGE THIS VALUE
        'sig_minus_idx': 0,     # LS1_SIG- DO NOT CHANGE THIS VALUE
        'excitation_voltage': 10.0,
        'sensitivity': 0.020
    },
    'LS2': {
        'enabled': False,
        'sig_plus_idx': 11,      # LS2_SIG+ DO NOT CHANGE THIS VALUE
        'sig_minus_idx': 10,     # LS2_SIG- DO NOT CHANGE THIS VALUE
        'excitation_voltage': 5.0,
        'sensitivity': 0.020
    },
    'LS3': {
        'enabled': False,
        'sig_plus_idx': 9,      # LS3_SIG+ DO NOT CHANGE THIS VALUE
        'sig_minus_idx': 8,     # LS3_SIG- DO NOT CHANGE THIS VALUE
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
        'sig_idx': 13,           # PT1_SIG DO NOT CHANGE THIS VALUE
        'excitation_voltage': 5.0,
        'V_max': 4.5,
        'V_min': 0.5,
        'V_span': 4.0,
        'P_min': 0.0,
        'P_max': 100.0
    },
    'PT2': {
        'enabled': False,
        'sig_idx': 12,           # PT2_SIG DO NOT CHANGE THIS VALUE
        'excitation_voltage': 5.0,
        'V_max': 4.5,
        'V_min': 0.5,
        'V_span': 4.0,
        'P_min': 0.0,
        'P_max': 100.0
    },
    'PT3': {
        'enabled': False,
        'sig_idx': 23,          # PT3_SIG DO NOT CHANGE THIS VALUE
        'excitation_voltage': 5.0,
        'V_max': 4.5,
        'V_min': 0.5,
        'V_span': 4.0,
        'P_min': 0.0,
        'P_max': 100.0
    },
    'PT4': {
        'enabled': False,
        'sig_idx': 22,          # PT4_SIG DO NOT CHANGE THIS VALUE
        'excitation_voltage': 5.0,
        'V_max': 4.5,
        'V_min': 0.5,
        'V_span': 4.0,
        'P_min': 0.0,
        'P_max': 100.0
    },
    'PT5': {
        'enabled': False,
        'sig_idx': 21,          # PT5_SIG DO NOT CHANGE THIS VALUE
        'excitation_voltage': 5.0,
        'V_max': 4.5,
        'V_min': 0.5,
        'V_span': 4.0,
        'P_min': 0.0,
        'P_max': 100.0
    },
    'PT6': {
        'enabled': False,
        'sig_idx': 20,          # PT6_SIG DO NOT CHANGE THIS VALUE
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
        'enabled': False,
        'V_leg1_idx': 16,       # RTD1_L1 DO NOT CHANGE THIS VALUE
        'V_leg2_idx': 14        # RTD1_L2 DO NOT CHANGE THIS VALUE
    },
    'RTD2': {
        'enabled': False,
        'V_leg1_idx': 11,       # RTD2_L1 DO NOT CHANGE THIS VALUE
        'V_leg2_idx': 10        # RTD2_L2 DO NOT CHANGE THIS VALUE
    }
}

