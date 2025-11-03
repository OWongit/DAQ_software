#!/usr/bin/env python3
import os
import time
import spidev
import gpiod
from gpiod.line import Direction, Value


class ADS124S08:
    """Minimal ADS124S08 driver for Raspberry Pi (SPI mode 1) + libgpiod v2."""

    # --- Register addresses (subset) ---
    REG_INPMUX = 0x02
    REG_PGA = 0x03
    REG_DATARATE = 0x04
    REG_REF = 0x05

    # --- Commands (subset) ---
    CMD_RESET = 0x06
    CMD_START = 0x08
    CMD_STOP = 0x0A
    CMD_RDATA = 0x12
    CMD_RDATAC = 0x14
    CMD_SDATAC = 0x16
    CMD_SFOCAL = 0x19  # self offset calibration (optional)

    AINCOM_CODE = 0x0C  # AINCOM value used in INPMUX (lower nibble)

    def __init__(self, spi_bus, spi_dev, gpiochip="/dev/gpiochip0", reset_pin=None, drdy_pin=None, start_pin=None, max_speed_hz=1_000_000):

        # --- SPI setup ---
        devpath = f"/dev/spidev{spi_bus}.{spi_dev}"
        if not os.path.exists(devpath):
            raise RuntimeError(f"{devpath} not found. Enable SPI and/or correct bus/dev.")
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_dev)  # (0,0) or (0,1)
        self.spi.mode = 0b01  # ADS124S08 requires mode 1
        self.spi.max_speed_hz = max_speed_hz
        self.spi.bits_per_word = 8

        # --- GPIO (libgpiod v2) ---
        self.reset_pin = reset_pin
        self.start_pin = start_pin
        self.drdy_pin = drdy_pin

        self.chip = gpiod.Chip(gpiochip)

        # request outputs
        self._req_out = None
        out_cfg = {}
        if reset_pin is not None:
            out_cfg[reset_pin] = gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)  # RESET high
        if start_pin is not None:
            out_cfg[start_pin] = gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE)  # START low
        if out_cfg:
            self._req_out = self.chip.request_lines(config=out_cfg, consumer="ads124_out")

        # request input (DRDY)
        self._req_in = None
        if drdy_pin is not None:
            self._req_in = self.chip.request_lines(config={drdy_pin: gpiod.LineSettings(direction=Direction.INPUT)}, consumer="ads124_in")

        time.sleep(0.005)

    # ----------------- Low-level helpers -----------------
    def _send_cmd(self, cmd):
        self.spi.xfer2([cmd])

    def wreg(self, addr, data_bytes):
        """Write n bytes starting at register 'addr'."""
        n = len(data_bytes)
        self.spi.xfer2([0x40 | (addr & 0x1F), (n - 1)] + list(data_bytes))

    def rreg(self, addr, n):
        """Read n bytes starting at register 'addr' -> returns list of bytes."""
        rx = self.spi.xfer2([0x20 | (addr & 0x1F), (n - 1)] + [0x00] * n)
        # response: [cmd, count, <n bytes>]
        return rx[2:]

    def hardware_reset(self):
        """Toggle RESET pin if provided; otherwise send RESET command."""
        if self._req_out and self.reset_pin is not None:
            self._req_out.set_value(self.reset_pin, Value.INACTIVE)  # RESET low
            time.sleep(0.001)
            self._req_out.set_value(self.reset_pin, Value.ACTIVE)  # RESET high
        else:
            self._send_cmd(self.CMD_RESET)
        time.sleep(0.005)

    def start(self):
        self._send_cmd(self.CMD_START)

    def stop(self):
        self._send_cmd(self.CMD_STOP)

    def wait_drdy(self, timeout_s=0.2):
        """Wait for DRDY low (active-low). If no DRDY line, just sleep."""
        if self._req_in is None or self.drdy_pin is None:
            time.sleep(timeout_s)
            return True
        t0 = time.time()
        while (time.time() - t0) < timeout_s:
            if self._req_in.get_value(self.drdy_pin) == Value.INACTIVE:
                return True
        return False

    def read_raw_sample(self):
        """Send RDATA and read 24-bit signed result."""
        rx = self.spi.xfer2([self.CMD_RDATA, 0x00, 0x00, 0x00])
        b2, b1, b0 = rx[1], rx[2], rx[3]
        code = (b2 << 16) | (b1 << 8) | b0
        # sign-extend 24-bit
        if code & 0x800000:
            code -= 1 << 24
        return code

    # ----------------- Config helpers -----------------
    def configure_basic(self, use_internal_ref=True, gain=1, data_rate=None):
        """
        Basic sane setup:
        - Optionally enable/select internal 2.5V reference.
        - Set PGA bypass/gain.
        - (Optional) set data rate if provided.
        """
        # PGA register
        if gain == 1:
            # PGA bypassed (gain=1)
            self.wreg(self.REG_PGA, [0x00])
        else:
            gain_map = {1: 0, 2: 1, 4: 2, 8: 3, 16: 4, 32: 5, 64: 6, 128: 7}
            if gain not in gain_map:
                raise ValueError("gain must be one of 1,2,4,8,16,32,64,128")
            # Enable PGA, set gain code
            self.wreg(self.REG_PGA, [(1 << 3) | gain_map[gain]])

        # Reference register
        if use_internal_ref:
            # Turn on internal 2.5V reference and select it.
            # Also keep external ref buffers disabled.
            # (Value chosen to match common TI app note settings.)
            self.wreg(self.REG_REF, [0x39])

        # Data rate (optional): if you know the code you want, write it here.
        if data_rate is not None:
            self.wreg(self.REG_DATARATE, [data_rate])

    def set_inpmux_single(self, ainp):
        """AINp = ainp (0..11), AINn = AINCOM."""
        if not (0 <= ainp <= 11):
            raise ValueError("ainp must be 0..11")
        val = ((ainp & 0x0F) << 4) | (self.AINCOM_CODE & 0x0F)
        self.wreg(self.REG_INPMUX, [val])

    @staticmethod
    def code_to_volts(code, vref=2.5, gain=1):
        """Convert 24-bit code to volts for bipolar transfer: ±Vref/gain."""
        FS = (1 << 23) - 1  # 0x7FFFFF
        return (code / FS) * (vref / gain)

    # ----------------- Convenience reads -----------------
    def read_voltage_single(self, ainp, vref=2.5, gain=1, settle_discard=True):
        """
        Set MUX to AINp vs AINCOM, wait for DRDY, optionally discard first sample
        after mux change, then read and return (code, volts).
        """
        self.set_inpmux_single(ainp)
        # Wait for a conversion with the new MUX; discard the first sample to settle
        if not self.wait_drdy(0.5):
            raise TimeoutError("DRDY timeout after MUX change")
        first = self.read_raw_sample()
        if settle_discard:
            if not self.wait_drdy(0.5):
                raise TimeoutError("DRDY timeout (settle discard)")
        code = self.read_raw_sample()
        volts = self.code_to_volts(code, vref=vref, gain=gain)
        return code, volts

    def close(self):
        try:
            self.spi.close()
        except Exception:
            pass
