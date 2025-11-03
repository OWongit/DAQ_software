"""
Mock (fake) spidev library for testing on a local machine.
"""
import random

class SpiDev:
    def __init__(self):
        self._mode = 0
        self._max_speed_hz = 500000
        self.bus = -1
        self.device = -1
        print("MockSpiDev: Created.")

    def open(self, bus, device):
        self.bus = bus
        self.device = device
        print(f"MockSpiDev: Opening bus {bus}, device {device}")

    def close(self):
        print(f"MockSpiDev: Closing b{self.bus}d{self.device}")

    def xfer2(self, data_list):
        """
        Simulates an SPI transfer.
        Returns dummy data appropriate for the command.
        """
        # RDATA command is [0x12, 0x00, 0x00, 0x00]
        if data_list[0] == 0x12 and len(data_list) == 4:
            # This is a read_raw_sample() call. Return 4 bytes.
            # [ignored, b2, b1, b0]
            val = random.randint(-0x7FFFFF, 0x7FFFFF) # Generate positive or negative
            
            # Convert to 24-bit two's complement
            if val < 0:
                val = (1 << 24) + val
                
            b2 = (val >> 16) & 0xFF
            b1 = (val >> 8) & 0xFF
            b0 = val & 0xFF
            
            # print(f"MockSpiDev: xfer2(RDATA) on b{self.bus}d{self.device}, returning [0x00, {b2:02x}, {b1:02x}, {b0:02x}]")
            return [0x00, b2, b1, b0]
        else:
            # This is a WREG or CMD
            # print(f"MockSpiDev: xfer2(CMD/WREG) on b{self.bus}d{self.device}, data: {data_list}")
            return [0x00] * len(data_list) # Return dummy bytes

    @property
    def mode(self):
        return self._mode
    @mode.setter
    def mode(self, val):
        self._mode = val

    @property
    def max_speed_hz(self):
        return self._max_speed_hz
    @max_speed_hz.setter
    def max_speed_hz(self, val):
        self._max_speed_hz = val

    @property
    def bits_per_word(self):
        return self._bits_per_word
    @bits_per_word.setter
    def bits_per_word(self, val):
        self._bits_per_word = val

