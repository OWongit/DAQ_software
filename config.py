"""
Sensor configuration file.
Hardcoded hardware values are defined here; all other settings (enabled,
sensitivity, max_load, P_min, P_max, ADC datarate, settle_discard) come from
settings.json. load_settings() must be called to populate LOAD_CELLS,
PRESSURE_TRANSDUCERS, RTDS, ADC_DATARATE_CODE, ADC_SETTLE_DISCARD.
"""

import json
import os

# ---------------------------
# ADC performance knobs (values set from settings.json in load_settings())
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
    "PT1 (5V)": {"ADC": 2, "SIG": 1, "excitation_voltage": 5.0, "V_max": 4.5, "V_min": 0.5, "V_span": 4.0},
    "PT2 (5V)": {"ADC": 2, "SIG": 0, "excitation_voltage": 5.0, "V_max": 4.5, "V_min": 0.5, "V_span": 4.0},
    "PT3 (5V)": {"ADC": 2, "SIG": 11, "excitation_voltage": 5.0, "V_max": 4.5, "V_min": 0.5, "V_span": 4.0},
    "PT4 (5V)": {"ADC": 2, "SIG": 10, "excitation_voltage": 5.0, "V_max": 4.5, "V_min": 0.5, "V_span": 4.0},
    "PT5 (5V)": {"ADC": 2, "SIG": 9, "excitation_voltage": 5.0, "V_max": 4.5, "V_min": 0.5, "V_span": 4.0},
    "PT6 (5V)": {"ADC": 2, "SIG": 8, "excitation_voltage": 5.0, "V_max": 4.5, "V_min": 0.5, "V_span": 4.0},
}

# RTD hardcoded values only
RTDS_HARDCODE = {
    "RTD1": {"ADC": 1, "L1": 4, "L2": 2},
    "RTD2": {"ADC": 2, "L1": 4, "L2": 2},
}

# Allowed unit values for settings validation (must match frontend unit options)
LOAD_CELL_UNITS = {"lbf", "lb", "lbs", "N", "kN", "kgf", "oz", "ton", "tonne", "g"}
PRESSURE_UNITS = {"Pa", "kPa", "MPa", "psi", "psig", "psia", "bar", "mbar", "inH2O", "ftH2O", "inHg", "mmHg", "atm", "torr", "psf"}
RTD_UNITS = {"°C", "°F", "K", "°R"}

# Merged config (hardcode + settings.json); set by load_settings()
LOAD_CELLS = {}
PRESSURE_TRANSDUCERS = {}
RTDS = {}


def get_settings_path():
    """Return the path to settings.json (next to this file)."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")


def _merge_sensor_config(hardcode_dict, data, key):
    """Merge hardcode dict with JSON data[key]; JSON values override. Returns merged dict."""
    json_section = data.get(key, {})
    return {name: {**hard, **json_section.get(name, {})} for name, hard in hardcode_dict.items()}


def load_settings():
    """
    Read settings.json and merge with hardcoded values. Set LOAD_CELLS,
    PRESSURE_TRANSDUCERS, RTDS, ADC_DATARATE_CODE, ADC_SETTLE_DISCARD on this module.
    Returns (load_cells_dict, pressure_transducers_dict, rtds_dict).
    """
    path = get_settings_path()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ADC
    adc = data.get("adc", {})
    if "datarate_code" in adc and 0 <= int(adc["datarate_code"]) <= 13:
        globals()["ADC_DATARATE_CODE"] = int(adc["datarate_code"])
    if "settle_discard" in adc:
        globals()["ADC_SETTLE_DISCARD"] = bool(adc["settle_discard"])

    # Merge sensor configs: hardcode + JSON (JSON wins for overlapping keys)
    merged_lc = _merge_sensor_config(LOAD_CELLS_HARDCODE, data, "load_cells")
    merged_pt = _merge_sensor_config(PRESSURE_TRANSDUCERS_HARDCODE, data, "pressure_transducers")
    merged_rtd = _merge_sensor_config(RTDS_HARDCODE, data, "rtds")

    globals()["LOAD_CELLS"] = merged_lc
    globals()["PRESSURE_TRANSDUCERS"] = merged_pt
    globals()["RTDS"] = merged_rtd
    return merged_lc, merged_pt, merged_rtd


def get_editable_settings():
    """
    Return current settings for the UI (what is stored in settings.json).
    Used by GET /api/settings.
    """
    path = get_settings_path()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        "adc": data.get("adc", {"datarate_code": 10, "settle_discard": True}),
        "load_cells": data.get("load_cells", {}),
        "pressure_transducers": data.get("pressure_transducers", {}),
        "rtds": data.get("rtds", {}),
    }
