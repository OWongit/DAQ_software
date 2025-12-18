import spidev
from gpiozero import OutputDevice
from time import sleep


start_pin = OutputDevice(17)
start_pin.on()
reset_pin = OutputDevice(22)
reset_pin.on()

sleep(2)

spi = spidev.SpiDev()

spi.open(0, 0)
spi.max_speed_hz = 100000
while True:
    print(spi.xfer2([0x12, 0x00, 0x00, 0x00]))
    sleep(1)
