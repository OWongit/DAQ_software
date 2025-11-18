"""
ads124s08_mock.py

Mock model of the Texas Instruments ADS124S08 24-bit delta-sigma ADC suitable
for exercising SPI driver code and higher-level logic without real hardware.

This module provides:

    - MockADS124S08SpiDevice:
        An SPI-level emulator that understands a subset of the real device
        commands (RESET, START, STOP, RREG, WREG, RDATA) and maintains
        a simple register map. Conversion results are generated from
        user-supplied "analog signal" callables.

The implementation is deliberately simplified but follows the key behaviors:
    * 24-bit two's-complement output format
    * INPMUX register selects the positive and negative inputs
    * Gain and data rate taken from the GAIN and DATARATE registers

You can use it together with `mock_spidev.SpiDev`:

    from mock_spidev import SpiDev, register_device
    from ads124s08_mock import MockADS124S08SpiDevice
    from signal_generator import sine_wave

    adc = MockADS124S08SpiDevice(
        signal_sources={0: sine_wave(amplitude=2.0, offset=2.5, freq_hz=1.0)}
    )
    register_device(0, 0, adc)

    spi = SpiDev()
    spi.open(0, 0)

    # Example: send RDATA command (0x12) and clock out three data bytes
    rx = spi.xfer2([0x12, 0x00, 0x00, 0x00])
    status_or_dummy = rx[0]
    msb, mid, lsb = rx[1], rx[2], rx[3]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
import math
import random


# --- Helpers for mapping between register fields and real units ----------------


GAIN_CODE_TO_VALUE = {
    0: 1,
    1: 2,
    2: 4,
    3: 8,
    4: 16,
    5: 32,
    6: 64,
    7: 128,
}

# DR[3:0] mapping to nominal samples-per-second
DR_CODE_TO_SPS = {
    0x0: 2.5,
    0x1: 5.0,
    0x2: 10.0,
    0x3: 16.6,
    0x4: 20.0,
    0x5: 50.0,
    0x6: 60.0,
    0x7: 100.0,
    0x8: 200.0,
    0x9: 400.0,
    0xA: 800.0,
    0xB: 1000.0,
    0xC: 2000.0,
    0xD: 4000.0,
    0xE: 4000.0,  # per datasheet, this code aliases 4000 SPS
    0xF: 4000.0,  # reserved; treat as 4000 SPS for simulation
}


def _twos_complement_24bit(value: int) -> int:
    """
    Normalize an integer into signed 24-bit two's complement range.

    Returns a Python int in the range [-2^23, 2^23-1].
    """
    value &= 0xFFFFFF
    if value & 0x800000:
        return value - (1 << 24)
    return value


def _encode_24bit(value: int) -> int:
    """
    Take a signed Python int and clamp it to the legal 24-bit range,
    then return it as an unsigned 24-bit value (0..0xFFFFFF).
    """
    if value > 0x7FFFFF:
        value = 0x7FFFFF
    elif value < -0x800000:
        value = -0x800000
    if value < 0:
        value = (1 << 24) + value
    return value & 0xFFFFFF


# --- Main SPI-level emulator ---------------------------------------------------


AnalogSignal = Callable[[float], float]  # t -> voltage (volts)


@dataclass
class MockADS124S08SpiDevice:
    """
    SPI-level mock of the ADS124S08.

    Parameters
    ----------
    signal_sources:
        Mapping from "analog node index" (0-11, plus optionally others) to a
        callable f(t_seconds) -> voltage_in_volts. The INPMUX register selects
        which indices are used as the positive and negative ADC inputs.

        For simple cases you can treat indices 0-11 as AIN0-AIN11.

    v_ref:
        Reference voltage used for conversion scaling, in volts. The real
        device commonly uses its internal 2.5-V reference.

    noise_lsb:
        Standard deviation of additive Gaussian noise in LSBs of the ADC
        output code. Use 0 for a noiseless model.

    time_step_mode:
        How simulated time advances:
            "by_data_rate" (default): dt = 1 / data_rate every conversion.
            "fixed": dt = fixed_dt on each conversion, ignoring data rate.

    fixed_dt:
        Time increment in seconds for time_step_mode="fixed".
    """

    signal_sources: Dict[int, AnalogSignal] = field(default_factory=dict)
    v_ref: float = 2.5
    noise_lsb: float = 0.0
    time_step_mode: str = "by_data_rate"
    fixed_dt: float = 0.01

    # Internal state
    registers: bytearray = field(init=False)
    converting: bool = field(default=False, init=False)
    _t: float = field(default=0.0, init=False)
    _last_code: int = field(default=0, init=False)

    NUM_REGISTERS: int = 0x12  # 0x00 .. 0x11 inclusive

    def __post_init__(self):
        # Initialize the register map with datasheet reset values where known.
        self.registers = bytearray(self.NUM_REGISTERS)
        self.reset()

    # --- Basic device behavior -------------------------------------------------

    def reset(self):
        """
        Reset the device to power-on defaults.
        """
        # Device ID register: use a fixed, arbitrary ID
        self.registers[0x00] = 0x00  # datasheet says "xxh" after reset
        self.registers[0x01] = 0x80  # STATUS
        self.registers[0x02] = 0x01  # INPMUX
        self.registers[0x03] = 0x00  # GAIN
        self.registers[0x04] = 0x14  # DATARATE
        self.registers[0x05] = 0x10  # REFMUX
        self.registers[0x06] = 0x00  # IDACMAG1
        self.registers[0x07] = 0xFF  # IDACMAG2
        self.registers[0x08] = 0x00  # VBIAS
        self.registers[0x09] = 0x10  # SYS register
        self.registers[0x0A] = 0x00  # OFCAL1
        self.registers[0x0B] = 0x00  # OFCAL2
        self.registers[0x0C] = 0x00  # OFCAL3
        self.registers[0x0D] = 0x00  # FSCAL1
        self.registers[0x0E] = 0x00  # FSCAL2
        self.registers[0x0F] = 0x40  # FSCAL3
        self.registers[0x10] = 0x00  # GPIO data
        self.registers[0x11] = 0x00  # GPIO config

        self.converting = False
        self._t = 0.0
        self._last_code = 0

    # --- SPI entry point -------------------------------------------------------

    def transfer(self, tx: List[int]) -> List[int]:
        """
        Main SPI entry point. This is called by mock_spidev.SpiDev.xfer2().

        The implementation assumes that each multibyte command sequence is
        contained entirely within a single transfer() call. This matches the
        style used in many simple ADS124S0x drivers.
        """
        rx: List[int] = []
        i = 0
        while i < len(tx):
            cmd = tx[i] & 0xFF

            # Control commands -------------------------------------------------
            if cmd in (0x00,):  # NOP
                rx.append(0x00)
                i += 1
            elif cmd in (0x02, 0x03):  # WAKEUP
                rx.append(0x00)
                i += 1
            elif cmd in (0x04, 0x05):  # POWERDOWN
                rx.append(0x00)
                self.converting = False
                i += 1
            elif cmd in (0x06, 0x07):  # RESET
                rx.append(0x00)
                self.reset()
                i += 1
            elif cmd in (0x08, 0x09):  # START
                rx.append(0x00)
                self.converting = True
                i += 1
            elif cmd in (0x0A, 0x0B):  # STOP
                rx.append(0x00)
                self.converting = False
                i += 1

            # Calibration commands (no-ops for this mock) ----------------------
            elif cmd in (0x16, 0x17, 0x19):  # SYOCAL, SYGCAL, SFOCAL
                rx.append(0x00)
                i += 1

            # RDATA command ----------------------------------------------------
            elif cmd in (0x12, 0x13):  # RDATA
                rx.append(0x00)  # status or dummy byte

                # Generate a fresh conversion result
                self._last_code = self._perform_conversion()

                code = _encode_24bit(self._last_code)
                msb = (code >> 16) & 0xFF
                mid = (code >> 8) & 0xFF
                lsb = code & 0xFF

                # For simplicity we always return exactly three data bytes,
                # regardless of how many dummy bytes were supplied.
                rx.extend([msb, mid, lsb])

                # Consume the rest of this transfer (any trailing dummy bytes)
                # while returning zeros for them so that the caller still gets
                # the correct number of bytes.
                remaining = len(tx) - (i + 1)
                if remaining > 3:
                    rx.extend([0x00] * (remaining - 3))
                i = len(tx)

            # RREG command -----------------------------------------------------
            elif (cmd & 0xE0) == 0x20 and (i + 1) < len(tx):
                start_addr = cmd & 0x1F
                count_minus_one = tx[i + 1] & 0x1F
                num_regs = count_minus_one + 1

                # Echo two dummy bytes for the command bytes
                rx.extend([0x00, 0x00])

                for offset in range(num_regs):
                    addr = start_addr + offset
                    if 0 <= addr < len(self.registers):
                        rx.append(self.registers[addr])
                    else:
                        rx.append(0x00)

                i += 2 + num_regs

            # WREG command -----------------------------------------------------
            elif (cmd & 0xE0) == 0x40 and (i + 1) < len(tx):
                start_addr = cmd & 0x1F
                count_minus_one = tx[i + 1] & 0x1F
                num_regs = count_minus_one + 1
                data_start = i + 2
                data_end = data_start + num_regs

                # Echo two dummy bytes for the command bytes
                rx.extend([0x00, 0x00])

                for offset in range(num_regs):
                    addr = start_addr + offset
                    if data_start + offset < len(tx):
                        value = tx[data_start + offset] & 0xFF
                        if 0 <= addr < len(self.registers):
                            self.registers[addr] = value

                i = min(len(tx), data_end)

            else:
                # Unknown command: just echo zeros for this byte
                rx.append(0x00)
                i += 1

        # Ensure RX length matches TX length
        if len(rx) < len(tx):
            rx.extend([0x00] * (len(tx) - len(rx)))
        elif len(rx) > len(tx):
            rx = rx[: len(tx)]

        return rx

    # --- Conversion modeling ---------------------------------------------------

    def _current_gain(self) -> float:
        gain_reg = self.registers[0x03] & 0x07  # GAIN[2:0]
        return float(GAIN_CODE_TO_VALUE.get(gain_reg, 1))

    def _current_data_rate(self) -> float:
        dr_reg = self.registers[0x04] & 0x0F  # DR[3:0]
        return float(DR_CODE_TO_SPS.get(dr_reg, 20.0))

    def _update_time(self):
        if self.time_step_mode == "fixed":
            self._t += float(self.fixed_dt)
        else:
            sps = self._current_data_rate()
            if sps <= 0:
                dt = 0.0
            else:
                dt = 1.0 / sps
            self._t += dt

    def _selected_inputs(self) -> tuple[int, int]:
        """
        Return (muxp_index, muxn_index) taken directly from the INPMUX register.

        The real device uses these four-bit codes to select from AIN0-AIN11,
        AINCOM, and several internal nodes. For simplicity, this mock treats
        the codes as indices into the signal_sources mapping.
        """
        inpmux = self.registers[0x02]
        muxp = (inpmux >> 4) & 0x0F
        muxn = inpmux & 0x0F
        return muxp, muxn

    def _sample_analog(self) -> float:
        """
        Sample the differential analog input voltage based on the currently
        selected MUX inputs and the provided signal_sources.
        """
        muxp, muxn = self._selected_inputs()

        def _default_signal(_: float) -> float:
            return 0.0

        vp_func = self.signal_sources.get(muxp, _default_signal)
        vn_func = self.signal_sources.get(muxn, _default_signal)

        vp = float(vp_func(self._t))
        vn = float(vn_func(self._t))
        return vp - vn

    def _voltage_to_code(self, vin: float) -> int:
        """
        Convert an analog differential input voltage (vin) to a signed 24-bit code
        using the ideal transfer function from the datasheet.

        For this mock we assume an ideal ADC with full-scale range FS = Vref / Gain.
        """
        gain = self._current_gain()
        if gain <= 0:
            gain = 1.0

        fs = self.v_ref / gain  # positive full-scale magnitude

        # Clip input to the valid range
        if vin <= -fs:
            return -0x800000
        if vin >= fs:
            return 0x7FFFFF

        # Map from [-fs, +fs] to signed code range [-2^23, 2^23-1]
        fraction = vin / fs  # -1.0 .. +1.0
        ideal_code = fraction * (2**23 - 1)

        # Add Gaussian noise in LSB units if requested
        if self.noise_lsb > 0.0:
            ideal_code += random.gauss(0.0, float(self.noise_lsb))

        return int(round(ideal_code))

    def _perform_conversion(self) -> int:
        """
        Simulate one ADC conversion and return the signed 24-bit result.
        """
        if not self.converting:
            # If conversions are stopped, just return the last code.
            return self._last_code

        self._update_time()
        vin = self._sample_analog()
        code = self._voltage_to_code(vin)
        return _twos_complement_24bit(code)
