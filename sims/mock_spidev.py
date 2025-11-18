"""
mock_spidev.py

Lightweight mock of the `spidev` library for testing without real SPI hardware.

Usage
-----
Register a mock device on a bus/chip-select pair and then open that device
through SpiDev:

    from mock_spidev import SpiDev, register_device
    from ads124s08_mock import MockADS124S08SpiDevice

    spi = SpiDev()
    adc = MockADS124S08SpiDevice(...)
    register_device(0, 0, adc)   # attach adc to bus 0, device 0
    spi.open(0, 0)

    data_out = [0x12, 0x00, 0x00, 0x00]  # example RDATA command
    data_in = spi.xfer2(data_out)

If no device is registered for a given (bus, device), the transfer returns
a list of zeros of the same length as the input.
"""

from __future__ import annotations

from typing import Callable, Dict, Tuple, Protocol, List, Optional


class SPIDeviceHandler(Protocol):
    """
    Protocol for mock SPI devices.

    Either implement this protocol:

        class MyDevice:
            def transfer(self, tx: list[int]) -> list[int]:
                ...

    Or just pass a simple callable(tx: list[int]) -> list[int] into register_device().
    """

    def transfer(self, tx: List[int]) -> List[int]:  # pragma: no cover - protocol
        ...


# (bus, device) -> handler
_attached_devices: Dict[Tuple[int, int], Callable[[List[int]], List[int]] | SPIDeviceHandler] = {}


def register_device(bus: int, device: int, handler: Callable[[List[int]], List[int]] | SPIDeviceHandler):
    """
    Attach a mock device to the given bus/device pair.

    The handler can either be:
        - A callable(tx_bytes) -> rx_bytes
        - An object with a .transfer(tx_bytes) -> rx_bytes method
    """
    _attached_devices[(bus, device)] = handler


def unregister_device(bus: int, device: int):
    """
    Detach any mock device from the given bus/device pair.
    """
    _attached_devices.pop((bus, device), None)


class SpiDev:
    """
    Minimal mock implementation of spidev.SpiDev.

    Only implements:
        - open(bus, device)
        - close()
        - xfer2(data, speed_hz=0, delay_us=0, bits_per_word=0)
        - xfer(...)
        - writebytes(data)
        - readbytes(length)

    Attributes like max_speed_hz and mode are stored but do not affect behavior.
    """

    def __init__(self):
        self.opened: bool = False
        self.bus: Optional[int] = None
        self.device: Optional[int] = None

        # Commonly-used attributes on real SpiDev
        self.max_speed_hz: int = 1_000_000
        self.mode: int = 0
        self.bits_per_word: int = 8
        self.cshigh: bool = False
        self.lsbfirst: bool = False
        self.threewire: bool = False

    def open(self, bus: int, device: int):
        self.bus = int(bus)
        self.device = int(device)
        self.opened = True

    def close(self):
        self.opened = False
        self.bus = None
        self.device = None

    def _do_transfer(self, data, speed_hz=0, bits_per_word=0):
        if not self.opened:
            raise IOError("SPI device not open")

        if speed_hz:
            self.max_speed_hz = int(speed_hz)
        if bits_per_word:
            self.bits_per_word = int(bits_per_word)

        handler = _attached_devices.get((self.bus, self.device))
        tx_list = list(int(b) & 0xFF for b in data)

        if handler is None:
            # No device attached: just return zeros
            return [0] * len(tx_list)

        # Support both callable and .transfer() style handlers
        if hasattr(handler, "transfer"):
            rx = handler.transfer(tx_list)  # type: ignore[attr-defined]
        else:
            rx = handler(tx_list)  # type: ignore[call-arg]

        if rx is None:
            rx = [0] * len(tx_list)

        rx_list = list(int(b) & 0xFF for b in rx)

        # Ensure length matches the input (pad or trim as needed)
        if len(rx_list) < len(tx_list):
            rx_list.extend([0] * (len(tx_list) - len(rx_list)))
        elif len(rx_list) > len(tx_list):
            rx_list = rx_list[: len(tx_list)]

        return rx_list

    def xfer2(self, data, speed_hz=0, delay_us=0, bits_per_word=0):
        # delay_us is ignored in this mock
        return self._do_transfer(data, speed_hz=speed_hz, bits_per_word=bits_per_word)

    def xfer(self, data, speed_hz=0, delay_us=0, bits_per_word=0):
        # Same behavior as xfer2 for this mock
        return self._do_transfer(data, speed_hz=speed_hz, bits_per_word=bits_per_word)

    def writebytes(self, data):
        self._do_transfer(data)
        return len(data)

    def readbytes(self, length: int):
        return self._do_transfer([0] * int(length))
