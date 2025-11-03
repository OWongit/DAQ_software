"""
Mock (fake) gpiod library for testing on a local machine.
"""

# --- Mock Enums ---
class Direction:
    INPUT = 1
    OUTPUT = 2

class Value:
    INACTIVE = 0
    ACTIVE = 1

# --- Mock Settings Class ---
class LineSettings:
    def __init__(self, direction=Direction.INPUT, output_value=Value.INACTIVE, **kwargs):
        self.direction = direction
        self.output_value = output_value
        print(f"MockGpiod: LineSettings created (dir={'OUT' if direction==Direction.OUTPUT else 'IN'}, val={'ACTIVE' if output_value==Value.ACTIVE else 'INACTIVE'})")

# --- Mock Request Object ---
class _MockRequest:
    """This is the object returned by chip.request_lines()"""
    def __init__(self, config, consumer):
        self._config = config
        self._consumer = consumer
        print(f"MockGpiod: Lines requested by '{consumer}'")
    
    def set_value(self, pin, value):
        val_str = "ACTIVE" if value == Value.ACTIVE else "INACTIVE"
        # This is very spammy, so it's commented out
        # print(f"MockGpiod: Setting pin {pin} to {val_str}")
        pass

    def get_value(self, pin):
        # This is the critical one for DRDY (Data Ready)
        # We must return INACTIVE (LOW) to signal that data is ready
        # so the wait_drdy() loop can exit.
        # print(f"MockGpiod: Getting value for pin {pin}, returning INACTIVE (data ready)")
        return Value.INACTIVE # Return 0 (INACTIVE / LOW)

    # ------------------------------------------------------------------
    # --- !! BUG FIX !! ---
    # Added the missing release() method that ADC_testable.py calls.
    # ------------------------------------------------------------------
    def release(self):
        """Mock function to simulate releasing GPIO lines."""
        print(f"MockGpiod: Releasing lines for '{self._consumer}'")
        pass

# --- Mock Chip Class ---
class Chip:
    def __init__(self, gpiochip):
        if "dev" not in gpiochip:
             print(f"MockGpiod: Warning! gpiochip should be a path like /dev/gpiochip0, but got {gpiochip}")
        print(f"MockGpiod: Opening Chip {gpiochip}")
    
    def request_lines(self, config, consumer):
        """Returns the mock request object that has .set_value() and .get_value()"""
        return _MockRequest(config, consumer)

# --- Mock 'line' submodule ---
class _MockLineModule:
    """Mocks the 'from gpiod.line import ...' structure"""
    def __init__(self):
        self.Direction = Direction
        self.Value = Value

line = _MockLineModule()

