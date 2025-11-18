"""
signal_generator.py

Utility functions to create realistic-looking analog voltage signals
for feeding into MockADS124S08SpiDevice. All voltages are clipped
into the [0 V, 5 V] range by default.
"""

from __future__ import annotations

from typing import Callable
import math
import random

AnalogSignal = Callable[[float], float]  # t -> voltage (volts)


def _clip(v: float, v_min: float = 0.0, v_max: float = 5.0) -> float:
    return max(v_min, min(v_max, v))


# ---------------------------------------------------------------------------
# More realistic, mildly random example signals for system testing
# ---------------------------------------------------------------------------


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
    Generic helper that builds a stateful, semi-random analog signal.

    - v(t) evolves with a "trend" slope (increasing, decreasing, or flat).
    - With probability ~mode_switch_rate per second, the trend changes.
    - With probability ~spike_rate per second, a small positive spike is added.
    - Noise is small and Gaussian (noise_std).
    - Output is always clipped to [v_min, v_max].

    This relies on t increasing over time (which is true for the ADS mock).
    """

    v = _clip(v0, v_min, v_max)
    last_t = None
    # current slope in V/s
    slope = 0.0

    def pick_new_slope() -> float:
        # 3 modes: up, down, flat
        mode = random.choice(["up", "down", "flat"])
        if mode == "flat":
            return 0.0
        mag = random.uniform(slope_min, slope_max)
        return mag if mode == "up" else -mag

    def signal(t: float) -> float:
        nonlocal v, last_t, slope

        # First call or non-monotonic t: just reset reference time
        if last_t is None or t <= last_t:
            last_t = t
            return v

        dt = t - last_t
        last_t = t

        # Maybe change trend (increasing / decreasing / flat)
        # Probability in this interval ~ mode_switch_rate * dt
        if random.random() < mode_switch_rate * dt:
            slope = pick_new_slope()

        # Apply trend
        dv = slope * dt
        v += dv

        # Keep v within "base" span around its current level
        # This avoids it pinning hard against v_min/v_max too often.
        v = _clip(v, v_min, v_max)

        # Maybe add a small upward spike (but not below current level)
        # Probability in this interval ~ spike_rate * dt
        if random.random() < spike_rate * dt:
            spike = random.uniform(0.0, spike_max)
            v = min(v + spike, v_max)

        # Add small noise
        if noise_std > 0.0:
            v += random.gauss(0.0, noise_std)

        v = _clip(v, v_min, v_max)
        return v

    return signal


def example1(
    offset: float = 2.5,
    span: float = 2.0,
    noise_std: float = 0.01,
    v_min: float = 0.0,
    v_max: float = 5.0,
) -> AnalogSignal:
    """
    Example 1: slow drifting signal with occasional small spikes.

    - Think "sensor that wanders a bit over time".
    - Gentle up/down trend, low noise, rare tiny bumps upward.
    """

    half_span = span / 2.0
    v0 = _clip(offset, v_min + 0.1, v_max - 0.1)

    return _stateful_signal(
        v0=v0,
        v_min=v_min,
        v_max=v_max,
        base_span=span,
        slope_min=0.01,  # V/s
        slope_max=0.05,  # V/s
        mode_switch_rate=0.1,  # ~0.1 switches per second
        spike_rate=0.05,  # occasional spikes
        spike_max=0.15,  # <= 150 mV spike
        noise_std=noise_std,
    )


def example2(
    offset: float = 2.0,
    span: float = 3.0,
    noise_std: float = 0.02,
    v_min: float = 0.0,
    v_max: float = 5.0,
) -> AnalogSignal:
    """
    Example 2: more "active" signal that tends to ramp up or down,
    sometimes flattening out, with moderate random spikes.

    - Good for testing filters and threshold logic.
    """

    v0 = _clip(offset, v_min + 0.2, v_max - 0.2)

    return _stateful_signal(
        v0=v0,
        v_min=v_min,
        v_max=v_max,
        base_span=span,
        slope_min=0.02,  # V/s
        slope_max=0.15,  # V/s
        mode_switch_rate=0.2,  # more frequent trend changes
        spike_rate=0.1,  # more spikes
        spike_max=0.3,  # up to 300 mV
        noise_std=noise_std,
    )


def example3(
    offset: float = 1.0,
    span: float = 4.0,
    noise_std: float = 0.015,
    v_min: float = 0.0,
    v_max: float = 5.0,
) -> AnalogSignal:
    """
    Example 3: mostly increasing or decreasing over long stretches, with
    occasional plateaus and small "jitter" spikes.

    - Think "warming or cooling temperature" with small disturbances.
    """

    v0 = _clip(offset, v_min + 0.2, v_max - 0.2)

    return _stateful_signal(
        v0=v0,
        v_min=v_min,
        v_max=v_max,
        base_span=span,
        slope_min=0.005,  # slower trend
        slope_max=0.05,
        mode_switch_rate=0.05,  # rare trend change
        spike_rate=0.02,  # rare spikes
        spike_max=0.2,
        noise_std=noise_std,
    )


def example_ran() -> AnalogSignal:
    """
    Random example signal: 33% chance of example1, example2, or example3.

    Call this ONCE per channel to get a signal function:
        sig = example_ran()
        v = sig(t)

    All examples share the same basic parameter signature, so we just pass
    these through to whichever one is randomly selected.
    """
    choices = (example1, example2, example3)
    chosen = random.choice(choices)
    return chosen(
        offset=random.uniform(0, 5),
        span=random.uniform(0, 5),
        noise_std=random.uniform(0, 0.03),
        v_min=0,
        v_max=random.uniform(0, 5),
    )
