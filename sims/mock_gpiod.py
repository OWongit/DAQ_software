"""
mock_gpiod.py

Lightweight mock of the `gpiod` library for testing without real GPIO hardware.

Implements a very small subset of the python-gpiod API that is commonly used
on Raspberry Pi:
    - Chip(name)
    - Chip.get_line(offset) -> Line
    - Line.request(...)
    - Line.set_value()
    - Line.get_value()
    - Line.release()

You can use it as a drop-in replacement by doing:

    import mock_gpiod as gpiod

or by naming this file `gpiod.py` and putting it before the real library
on PYTHONPATH when running tests.
"""

from dataclasses import dataclass
from typing import Dict, Optional


class Direction:
    INPUT = "input"
    OUTPUT = "output"


class Value:
    INACTIVE = 0  # line is inactive (high for active-low DRDY)
    ACTIVE = 1  # line is active   (low for active-low DRDY)


@dataclass
class LineSettings:
    """
    Very small stand-in for gpiod.LineSettings.

    Only the fields that ADS124S08 uses are modeled:
        - direction
        - output_value  (for outputs)
    """

    direction: str = Direction.INPUT
    output_value: int = Value.INACTIVE


class LinesRequest:
    """
    Represents a set of requested GPIO lines.

    Implements:
        set_value(offset, Value)
        get_value(offset) -> Value
        release()
    """

    def __init__(self, config: Dict[int, LineSettings], consumer: Optional[str] = None):
        self.consumer = consumer
        # Store current values for each line
        self._values: Dict[int, int] = {}
        for offset, settings in config.items():
            if settings.direction == Direction.OUTPUT:
                self._values[offset] = settings.output_value
            else:
                # For inputs (like DRDY), default to INACTIVE so wait_drdy() succeeds
                self._values[offset] = Value.INACTIVE

    def set_value(self, offset: int, value: int):
        self._values[offset] = value

    def get_value(self, offset: int) -> int:
        # For inputs we just return whatever is stored (default INACTIVE)
        return self._values.get(offset, Value.INACTIVE)

    def release(self):
        self._values.clear()


class Chip:
    """
    Minimal mock of gpiod.Chip for the ADS124S08 driver.

    Used as:
        chip = gpiod.Chip("/dev/gpiochip0")
        req_out = chip.request_lines(config={...}, consumer="ads124_out")
    """

    def __init__(self, name: str = "/dev/gpiochip0"):
        self.name = name

    def request_lines(self, config: Dict[int, LineSettings], consumer: Optional[str] = None) -> LinesRequest:
        return LinesRequest(config=config, consumer=consumer)

    def close(self):
        # Nothing to do in the mock
        pass
