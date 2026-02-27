"""
Sensor configuration file.
Hardcoded hardware values are defined here; all editable settings are held
in memory (initially loaded from _DEFAULTS).  load_settings() must be called
once at startup to populate LOAD_CELLS, PRESSURE_TRANSDUCERS, RTDS,
ADC_DATARATE_CODE, and ADC_SETTLE_DISCARD.
"""

import copy

# ---------------------------
# ADC performance knobs (set by load_settings())
# ---------------------------
ADC_DATARATE_CODE = 10
ADC_SETTLE_DISCARD = True

# Load Cell hardcoded values only (ADC, SIG+, SIG-, excitation_voltage)
LOAD_CELLS_HARDCODE = {
    "LC1 (10V)": {"ADC": 1, "SIG+": 1, "SIG-": 0, "excitation_voltage": 10.0},
    "LC2 (5V)": {"ADC": 1, "SIG+": 11, "SIG-": 10, "excitation_voltage": 5.0},
    "LC3 (5V)": {"ADC": 1, "SIG+": 9, "SIG-": 8, "excitation_voltage": 5.0},
}

# Pressure Transducer hardcoded values only
PRESSURE_TRANSDUCERS_HARDCODE = {
    "PT1": {"ADC": 2, "SIG": 1, "excitation_voltage": 5.0, "V_max": 4.5, "V_min": 0.5, "V_span": 4.0},
    "PT2": {"ADC": 2, "SIG": 0, "excitation_voltage": 5.0, "V_max": 4.5, "V_min": 0.5, "V_span": 4.0},
    "PT3": {"ADC": 2, "SIG": 11, "excitation_voltage": 5.0, "V_max": 4.5, "V_min": 0.5, "V_span": 4.0},
    "PT4": {"ADC": 2, "SIG": 10, "excitation_voltage": 5.0, "V_max": 4.5, "V_min": 0.5, "V_span": 4.0},
    "PT5": {"ADC": 2, "SIG": 9, "excitation_voltage": 5.0, "V_max": 4.5, "V_min": 0.5, "V_span": 4.0},
    "PT6": {"ADC": 2, "SIG": 8, "excitation_voltage": 5.0, "V_max": 4.5, "V_min": 0.5, "V_span": 4.0},
}

# RTD hardcoded values only
RTDS_HARDCODE = {
    "RTD1": {"ADC": 1, "L1": 4, "L2": 2},
    "RTD2": {"ADC": 2, "L1": 4, "L2": 2},
}

# Allowed unit values for settings validation (must match frontend unit options)
LOAD_CELL_UNITS = {"N", "kN", "lbf", "gf", "kgf"}
PRESSURE_UNITS = {"psi", "Pa", "kPa", "bar", "mbar"}
RTD_UNITS = {"°C", "°F", "K"}

# Merged config (hardcode + editable); set by load_settings()
LOAD_CELLS = {}
PRESSURE_TRANSDUCERS = {}
RTDS = {}

# ---------------------------------------------------------------------------
# Defaults -- the values that were formerly in settings.json, now baked in.
# ---------------------------------------------------------------------------
_DEFAULTS = {
    "adc": {
        "datarate_code": 7,
        "settle_discard": True,
    },
    "load_cells": {
        "LC1 (10V)": {"display_name": "", "unit": "N", "enabled": False, "sensitivity": 0.02, "max_load": 1000, "offset": 0},
        "LC2 (5V)":  {"display_name": "", "unit": "N", "enabled": False, "sensitivity": 0.02, "max_load": 200,  "offset": 0},
        "LC3 (5V)":  {"display_name": "", "unit": "N", "enabled": False, "sensitivity": 0.02, "max_load": 200,  "offset": 0},
    },
    "pressure_transducers": {
        "PT1": {"display_name": "", "unit": "psi", "enabled": False, "P_min": 0, "P_max": 2000, "offset": 0},
        "PT2": {"display_name": "", "unit": "psi", "enabled": False, "P_min": 0, "P_max": 2000, "offset": 0},
        "PT3": {"display_name": "", "unit": "psi", "enabled": False, "P_min": 0, "P_max": 2000, "offset": 0},
        "PT4": {"display_name": "", "unit": "psi", "enabled": False, "P_min": 0, "P_max": 2000, "offset": 0},
        "PT5": {"display_name": "", "unit": "psi", "enabled": False, "P_min": 0, "P_max": 2000, "offset": 0},
        "PT6": {"display_name": "", "unit": "psi", "enabled": False, "P_min": 0, "P_max": 2000, "offset": 0},
    },
    "rtds": {
        "RTD1": {"display_name": "", "unit": "\u00b0C", "enabled": False, "offset": 0},
        "RTD2": {"display_name": "", "unit": "\u00b0C", "enabled": False, "offset": 0},
    },
}

# In-memory settings state
_current_settings = None
_config_file_name = None


def set_config_file_name(name):
    global _config_file_name
    _config_file_name = name


def get_config_file_name():
    return _config_file_name


def _merge_sensor_config(hardcode_dict, data, key):
    """Merge hardcode dict with data[key]; data values override. Returns merged dict."""
    json_section = data.get(key, {})
    return {name: {**hard, **json_section.get(name, {})} for name, hard in hardcode_dict.items()}


def load_settings(data=None):
    """
    Apply settings to this module's globals.  If *data* is provided (dict with
    adc / load_cells / pressure_transducers / rtds) use it; otherwise fall back
    to _DEFAULTS.  Also stores the editable portion in _current_settings.
    Returns (load_cells_dict, pressure_transducers_dict, rtds_dict).
    """
    global _current_settings

    if data is None:
        data = copy.deepcopy(_current_settings) if _current_settings is not None else copy.deepcopy(_DEFAULTS)

    # ADC
    adc = data.get("adc", {})
    if "datarate_code" in adc and 0 <= int(adc["datarate_code"]) <= 13:
        globals()["ADC_DATARATE_CODE"] = int(adc["datarate_code"])
    if "settle_discard" in adc:
        globals()["ADC_SETTLE_DISCARD"] = bool(adc["settle_discard"])

    # Merge sensor configs: hardcode + editable (editable wins for overlapping keys)
    merged_lc = _merge_sensor_config(LOAD_CELLS_HARDCODE, data, "load_cells")
    merged_pt = _merge_sensor_config(PRESSURE_TRANSDUCERS_HARDCODE, data, "pressure_transducers")
    merged_rtd = _merge_sensor_config(RTDS_HARDCODE, data, "rtds")

    globals()["LOAD_CELLS"] = merged_lc
    globals()["PRESSURE_TRANSDUCERS"] = merged_pt
    globals()["RTDS"] = merged_rtd

    _current_settings = {
        "adc": data.get("adc", copy.deepcopy(_DEFAULTS["adc"])),
        "load_cells": data.get("load_cells", {}),
        "pressure_transducers": data.get("pressure_transducers", {}),
        "rtds": data.get("rtds", {}),
    }

    return merged_lc, merged_pt, merged_rtd


def get_editable_settings():
    """
    Return current in-memory settings for the UI.
    If load_settings() has not been called yet, returns a copy of the defaults.
    """
    if _current_settings is None:
        return copy.deepcopy(_DEFAULTS)
    return copy.deepcopy(_current_settings)
