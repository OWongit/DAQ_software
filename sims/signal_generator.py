"""
sensor_signal_generator.py

Utility functions to create realistic-looking analog voltage signals for
the specific sensor types defined in sensors.py:

    - Load_Cell          -> differential pair (sig+, sig-)
    - Pressure_Transducer -> single-ended sig_voltage
    - RTD                -> two lead voltages (V_lead1, V_lead2)

Each factory returns stateful callables of the form:

    v = signal(t)   # t in seconds -> voltage in volts

intended to be used in the same way as signal_generator.example1/2/3.
"""

from __future__ import annotations

from typing import Callable, Tuple
import random

AnalogSignal = Callable[[float], float]
SignalPair = Tuple[AnalogSignal, AnalogSignal]


def _clip(v: float, v_min: float = 0.0, v_max: float = 5.0) -> float:
    """Clamp v into [v_min, v_max]."""
    return max(v_min, min(v_max, v))


def _stateful_signal(
    *,
    v0: float,
    v_min: float,
    v_max: float,
    base_span: float,
    slope_min: float,
    slope_max: float,
    mode_switch_rate: float,
    spike_rate: float,
    spike_max: float,
    noise_std: float,
) -> AnalogSignal:
    """
    Generic helper that builds a stateful, semi-random 1-D signal.

    Behavior is the same as signal_generator._stateful_signal, but here
    "v" can represent load, pressure, or temperature instead of strictly
    a voltage.

    - v(t) evolves with a trend slope (up, down, or flat).
    - With probability ~mode_switch_rate per second, the trend changes.
    - With probability ~spike_rate per second, a small positive step is added.
    - Small Gaussian noise (noise_std) is applied each step.
    - Output is always clipped to [v_min, v_max].

    Assumes t is monotonically increasing (true for the ADS mock).
    """

    v = _clip(v0, v_min, v_max)
    last_t = None
    slope = 0.0  # units per second

    def pick_new_slope() -> float:
        if random.random() < 0.8:  # % chance to be flat
            return 0.0
        mode = random.choice(["up", "down"])
        mag = random.uniform(slope_min, slope_max)
        return mag if mode == "up" else -mag

    def signal(t: float) -> float:
        nonlocal v, last_t, slope

        # First call or non-monotonic t: don't advance the state
        if last_t is None or t <= last_t:
            last_t = t
            return v

        dt = t - last_t
        last_t = t

        # Occasionally change trend (up / down / flat)
        if random.random() < mode_switch_rate * dt:
            slope = pick_new_slope()

        # Apply trend
        v += slope * dt
        v = _clip(v, v_min, v_max)

        # Occasional positive "step" in the underlying quantity
        if random.random() < spike_rate * dt:
            v = min(v + random.uniform(0.0, spike_max), v_max)

        # Small Gaussian noise in the physical quantity
        if noise_std > 0.0:
            v += random.gauss(0.0, noise_std)

        v = _clip(v, v_min, v_max)
        return v

    return signal


# ---------------------------------------------------------------------------
# Load cell: differential sig+ / sig- voltages
# ---------------------------------------------------------------------------


def make_load_cell_signal_pair(
    *,
    max_load: float,
    sensitivity: float = 0.0020,  # V/V (2 mV/V)
    excitation_voltage: float = 5.0,
    common_mode: float | None = None,
    noise_std_volts: float = 1e-3,
) -> SignalPair:
    """
    Build a pair of AnalogSignals (sig_plus, sig_minus) for a single load cell.

    The generated differential voltage follows the inverse of the logic in
    sensors.Load_Cell._calculate_force(), i.e.:

        force = (v_diff / (excitation * sensitivity)) * max_load

    so that feeding these signals into Load_Cell.read(...) will yield a
    force that closely tracks the underlying "true" load with some noise.

    Args:
        max_load:
            Full-scale load used by the Load_Cell instance.
        sensitivity:
            Load cell sensitivity in V/V (2 mV/V by default).
        excitation_voltage:
            Excitation / supply voltage applied to the bridge.
        common_mode:
            Nominal common-mode voltage of the bridge output.
            Defaults to excitation_voltage / 2.0.
        noise_std_volts:
            Per-channel Gaussian noise (standard deviation) added on top of
            ideal sig+ / sig- voltages.
    """

    if common_mode is None:
        common_mode = excitation_voltage / 2.0

    load_range = max_load
    load0 = 0.1 * max_load  # start at ~10% of full scale

    # Underlying "true" load in engineering units (e.g., kg, lbf)
    load_signal = _stateful_signal(
        v0=load0,
        v_min=0.0,
        v_max=max_load,
        base_span=load_range,
        slope_min=0.01 * max_load,   # load units / s
        slope_max=0.05 * max_load,
        mode_switch_rate=0.05,       # occasional direction changes
        spike_rate=0.02,             # occasional step changes in load
        spike_max=0.1 * max_load,
        noise_std=0.005 * max_load,
    )

    def _voltages_from_load(t: float) -> Tuple[float, float]:
        load = load_signal(t)

        # Convert load -> fraction of full scale
        if max_load > 0:
            ratio = load / max_load
        else:
            ratio = 0.0

        # Allow slight overshoot beyond full scale
        ratio = max(0.0, min(ratio, 1.1))

        # Invert Load_Cell._calculate_force():
        #   force = (v_diff / (excitation * sensitivity)) * max_load
        #   => v_diff = (force / max_load) * excitation * sensitivity
        v_diff = ratio * excitation_voltage * sensitivity

        v_p = common_mode + 0.5 * v_diff
        v_m = common_mode - 0.5 * v_diff
        return v_p, v_m

    def sig_plus(t: float) -> float:
        v_p, _ = _voltages_from_load(t)
        v_p += random.gauss(0.0, noise_std_volts)
        return _clip(v_p, 0.0, excitation_voltage)

    def sig_minus(t: float) -> float:
        # If called with the same t as sig_plus, load_signal(t) does not
        # advance its internal state and we get the same underlying load
        # (just with independent channel noise).
        _, v_m = _voltages_from_load(t)
        v_m += random.gauss(0.0, noise_std_volts)
        return _clip(v_m, 0.0, excitation_voltage)

    return sig_plus, sig_minus


# ---------------------------------------------------------------------------
# Pressure transducer: single-ended sig_voltage
# ---------------------------------------------------------------------------


def make_pressure_transducer_signal(
    *,
    P_min: float,
    P_max: float,
    V_min: float = 0.5,
    V_span: float = 4.0,
    excitation_voltage: float = 5.0,
    noise_std_volts: float = 5e-3,
) -> AnalogSignal:
    """
    Build an AnalogSignal for a single pressure transducer.

    The voltage mapping is the exact inverse of the logic in
    sensors.Pressure_Transducer._calculate_pressure():

        pressure = (V - V_min) * (P_range / V_span) + P_min

    so that feeding the generated sig_voltage into
    Pressure_Transducer.read(...) will yield a pressure that tracks the
    underlying "true" pressure signal.
    """

    pressure_range = P_max - P_min
    if pressure_range <= 0.0:
        raise ValueError("P_max must be greater than P_min")

    V_max = V_min + V_span

    # Underlying "true" pressure in engineering units
    p0 = P_min + 0.1 * pressure_range
    pressure_signal = _stateful_signal(
        v0=p0,
        v_min=P_min,
        v_max=P_max,
        base_span=pressure_range,
        slope_min=0.02 * pressure_range,  # units / s
        slope_max=0.10 * pressure_range,
        mode_switch_rate=0.10,
        spike_rate=0.10,
        spike_max=0.10 * pressure_range,
        noise_std=0.01 * pressure_range,
    )

    def sig_voltage(t: float) -> float:
        p = pressure_signal(t)
        # Inverse of _calculate_pressure:
        #   pressure = (V - V_min) * (P_range / V_span) + P_min
        #   => V = V_min + (pressure - P_min) * (V_span / P_range)
        v_ideal = V_min + (p - P_min) * (V_span / pressure_range)
        v = v_ideal + random.gauss(0.0, noise_std_volts)
        return _clip(v, 0.0, max(excitation_voltage, V_max))

    return sig_voltage


# ---------------------------------------------------------------------------
# RTD: two lead voltages (V_lead1, V_lead2)
# ---------------------------------------------------------------------------


def make_rtd_signal_pair(
    *,
    T_min: float = -20.0,
    T_max: float = 150.0,
    T0: float = 0.0,
    R0: float = 100.0,      # Pt100 nominal resistance at T0
    alpha: float = 0.00385, # linear temp coefficient
    I_exc: float = 1e-3,    # 1 mA excitation current
    lead_resistance: float = 1.0,  # ohms per lead
    noise_std_volts: float = 2e-4,
) -> SignalPair:
    """
    Build a pair of AnalogSignals (V_lead1, V_lead2) for an RTD input.

    The RTD temperature calculation in sensors.RTD is not implemented yet,
    but these voltages are shaped to look roughly like a Pt100 driven with
    a constant current source, with a small, slowly varying temperature
    trend and a tiny differential between the two leads.
    """

    temp_range = T_max - T_min
    T_start = max(T_min, min(T0, T_max))

    temp_signal = _stateful_signal(
        v0=T_start,
        v_min=T_min,
        v_max=T_max,
        base_span=temp_range,
        slope_min=0.1,   # degC / s
        slope_max=0.5,
        mode_switch_rate=0.02,
        spike_rate=0.01,
        spike_max=2.0,   # occasional small temp steps
        noise_std=0.05,
    )

    def _rtd_voltage_from_temp(T: float) -> float:
        # Simple linear Pt100 model: R(T) = R0 * (1 + alpha * (T - T0))
        R_T = R0 * (1.0 + alpha * (T - T0))
        return I_exc * R_T

    # Typical lead drop so V_lead1 / V_lead2 are close but not identical
    lead_drop = I_exc * lead_resistance

    def V_lead1(t: float) -> float:
        T = temp_signal(t)
        v_rtd = _rtd_voltage_from_temp(T)
        v = v_rtd + 0.5 * lead_drop + random.gauss(0.0, noise_std_volts)
        return _clip(v, 0.0, 5.0)

    def V_lead2(t: float) -> float:
        # Same underlying temperature, slightly different lead drop
        T = temp_signal(t)
        v_rtd = _rtd_voltage_from_temp(T)
        v = v_rtd - 0.5 * lead_drop + random.gauss(0.0, noise_std_volts)
        return _clip(v, 0.0, 5.0)

    return V_lead1, V_lead2
