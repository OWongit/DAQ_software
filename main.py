import Data.Collection as ADC
import time


def main():

    print("Initializing DAQ...")
    ADC.init_DAQ()  # The collection file needs to include an object that can be made twice for the two different ADCs.
    # We should ultimately be able to feed in different pins as parameters for configuring each of the ADC objects.
    # I believe that currently the .read_voltage() probably gets only 1 analog input, we need to read 5+ analog inputs from a single ADC ultamitely.
    try:
        while True:
            print("V: " + str(ADC.read_voltage) + "  Time: " + time.time())
    finally:
        ADC.shutdown_DAQ()


if __name__ == "__main__":
    main()
