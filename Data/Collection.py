import time
import spidev
import RPi.GPIO as GPIO

# ----- User-configurable parameters -----
VREF = 3.3  # Internal reference voltage (V)
PGA_GAIN = 1  # PGA gain setting
SPS_DELAY = 1 / 50.0  # Approximate delay between conversions (sec)

# ----- GPIO pin assignments (BCM numbering) -----
PIN_CS = 17  # manual chip-select
PIN_START = 27  # START/SYNC pin
PIN_DRDY = 22  # DOUT/DRDY data-ready output
spi = spidev.SpiDev()


def read_voltage():
    while GPIO.input(PIN_DRDY):
        time.sleep(0.001)

    # Clock out 3 data bytes (MSB first) :contentReference[oaicite:5]{index=5}
    GPIO.output(PIN_CS, GPIO.LOW)
    raw_bytes = spi.xfer2([0x00, 0x00, 0x00])
    GPIO.output(PIN_CS, GPIO.HIGH)

    # Combine bytes and sign-extend 24→32 bits :contentReference[oaicite:6]{index=6}
    raw_code = (raw_bytes[0] << 16) | (raw_bytes[1] << 8) | raw_bytes[2]
    if raw_code & 0x800000:
        raw_code -= 1 << 24

    # Scale to voltage: raw/(2^23-1) * (VREF/PGA_GAIN) :contentReference[oaicite:7]{index=7}
    voltage = (raw_code / float(0x7FFFFF)) * (VREF / PGA_GAIN)

    return voltage


def init_DAQ():
    # ----- Setup SPI (bus=0, device=0) -----
    spi.open(0, 0)
    spi.max_speed_hz = 500000
    spi.mode = 0b01  # CPOL=0, CPHA=1 :contentReference[oaicite:4]{index=4}
    spi.no_cs = True  # we control CS by GPIO

    # ----- Setup GPIO -----
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_CS, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(PIN_START, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PIN_DRDY, GPIO.IN)

    # ----- Initialize ADC: set input mux (AIN0–AIN1) and PGA=1 -----
    # WREG command: 0x40 | reg_addr,  num_regs-1,  data...
    # Here, reg0 = INPMUX, reg1 = PGA/IDAC
    mux_reg = 0x01  # INPMUX = AIN0 (P) / AIN1 (N)
    pga_reg = 0x00  # PGA gain=1, SYS delay default
    GPIO.output(PIN_CS, GPIO.LOW)
    spi.xfer2([0x40 | 0x00, 0x01, mux_reg, pga_reg])  # WREG to register 0  # write 2 registers (1 = count-1)
    GPIO.output(PIN_CS, GPIO.HIGH)
    time.sleep(0.1)

    # ----- Start continuous conversions -----
    GPIO.output(PIN_START, GPIO.HIGH)


def shutdown_DAQ():
    spi.close()
    GPIO.cleanup()
