import spidev
import gpiod
import time


class ADS124S08:
    def __init__(self, spi_bus, spi_dev, gpiochip="gpiochip4", reset_pin=None, drdy_pin=None, start_pin=None, max_speed_hz=1_000_000):
        # SPI setup
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_dev)  # e.g. (0,0) or (0,1)
        self.spi.mode = 0b01  # ADS124S08 needs SPI mode 1
        self.spi.max_speed_hz = max_speed_hz
        self.spi.bits_per_word = 8

        # GPIO setup
        self.chip = gpiod.Chip(gpiochip)

        self.reset_line = None
        if reset_pin is not None:
            self.reset_line = self.chip.get_line(reset_pin)
            self.reset_line.request(consumer="ads124_reset", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[1])

        self.start_line = None
        if start_pin is not None:
            self.start_line = self.chip.get_line(start_pin)
            self.start_line.request(consumer="ads124_start", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])

        self.drdy_line = None
        if drdy_pin is not None:
            self.drdy_line = self.chip.get_line(drdy_pin)
            self.drdy_line.request(consumer="ads124_drdy", type=gpiod.LINE_REQ_DIR_IN)

        time.sleep(0.005)

    def hardware_reset(self):
        if self.reset_line:
            self.reset_line.set_value(0)
            time.sleep(0.001)
            self.reset_line.set_value(1)
            time.sleep(0.005)

    def start_conversions(self):
        # START command = 0x08
        self.spi.xfer2([0x08])

    def wait_drdy(self, timeout_s=0.1):
        if self.drdy_line is None:
            time.sleep(timeout_s)
            return True
        t0 = time.time()
        while (time.time() - t0) < timeout_s:
            if self.drdy_line.get_value() == 0:
                return True
        return False

    def read_raw_sample(self):
        # RDATA command = 0x12 then clock out 3 data bytes
        rx = self.spi.xfer2([0x12, 0x00, 0x00, 0x00])
        b2, b1, b0 = rx[1], rx[2], rx[3]
        code = (b2 << 16) | (b1 << 8) | b0
        if code & 0x800000:
            code -= 1 << 24  # sign extend
        return code


def main():
    GPIOCHIP = "gpiochip4"  # On Pi 5 this is commonly the main 0-27 header bank

    # ADC1 on /dev/spidev0.0 (CE0 = GPIO8)
    adc1 = ADS124S08(
        spi_bus=0,
        spi_dev=0,
        gpiochip=GPIOCHIP,
        reset_pin=17,
        drdy_pin=25,
        start_pin=27,  # could also drive ADC2's START here if you tie them
    )

    # ADC2 on /dev/spidev0.1 (CE1 = GPIO7)

    adc1.hardware_reset()

    adc1.start_conversions()

    while True:
        if adc1.wait_drdy():
            raw1 = adc1.read_raw_sample()
            print(f"ADC1 raw={raw1}")
        time.sleep(0.1)


if __name__ == "__main__":
    main()
