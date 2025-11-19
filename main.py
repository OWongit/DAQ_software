import os
import time
from datetime import datetime

from ADC import ADS124S08
from data_logger import DataLogger
import sensors
import config

# If using simulated hardware type: "export USE_MOCK_HW=1" in the terminal.
def initialize_simulated_hardware():
    import sims.mock_spidev as mock_spidev
    from sims.ads124s08_mock import MockADS124S08SpiDevice
    from sims.signal_generator import example_ran
    skip_ains = (3, 5, 6, 7)  # skip ain3 and ain5 as IDAC lines
    
    adc1_sources = {i: example_ran() for i in range(12) if i not in skip_ains}
    adc2_sources = {i: example_ran() for i in range(12) if i not in skip_ains}

    # Create the mock SPI-level ADC devices
    adc1_device = MockADS124S08SpiDevice(signal_sources=adc1_sources, v_ref=5)
    adc2_device = MockADS124S08SpiDevice(signal_sources=adc2_sources, v_ref=5)

    # Attach them to SPI bus 0, chip selects 0 and 1
    mock_spidev.register_device(0, 0, adc1_device)
    mock_spidev.register_device(0, 1, adc2_device)


def main():
    GPIOCHIP = "/dev/gpiochip0"  # Pi Zero/3/4; adjust if needed

    script_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(script_dir, "data")

    logger = DataLogger(base_dir=save_dir)

    # Initialize sensor objects based on config
    sensor_labels, load_cells, pressure_transducers, rtds = sensors.initialize_sensors()

    adc1 = ADS124S08(id=1, spi_bus=0, spi_dev=0, gpiochip=GPIOCHIP, reset_pin=17, drdy_pin=25, start_pin=27, max_speed_hz=1_000_000)
    adc2 = ADS124S08(id=2, spi_bus=0, spi_dev=1, gpiochip=GPIOCHIP, reset_pin=22, drdy_pin=24, start_pin=26, max_speed_hz=1_000_000)

    try:
        # Reset and basic config
        adc1.hardware_reset()
        adc2.hardware_reset()
        adc1.configure_basic(use_internal_ref=False, gain=1)
        adc2.configure_basic(use_internal_ref=False, gain=1)

        # Start conversions (continuous)
        adc1.start()
        adc2.start()

        VREF = 5
        GAIN = 1

        while True:
            now = datetime.now()
            time_now_str = now.strftime("%H:%M:%S.%f")

            voltages1 = adc1.read_voltage_full(vref=VREF, gain=GAIN)
            voltages2 = adc2.read_voltage_full(vref=VREF, gain=GAIN)
            # [LS1_SIG-,LS1_SIG+,RTD1_L2,RTD1_L1,LS3_SIG-,LS3_SIG+,LS2_SIG-,LS2_SIG+,PT2_SIG,PT1_SIG,RTD2_L2,RTD2_L1,PT6_SIG,PT5_SIG,PT4_SIG,PT3_SIG]
            voltages = voltages1 + voltages2
            # Log the raw float data (unchanged)
            row_data = [time_now_str] + voltages
            logger.log_row(row_data)
            time.sleep(0.1)

            # Read sensor values
            sensor_values = sensors.read_sensors(voltages, load_cells, pressure_transducers, rtds)
            print(f"{time_now_str} - Voltages: {voltages}")
            print(f"{time_now_str} - Labels: {sensor_labels}")
            print(f"{time_now_str} - Sensors: {sensor_values}")

    except KeyboardInterrupt:
        pass
    finally:
        adc1.stop()
        adc2.stop()
        adc1.close()
        adc2.close()


if __name__ == "__main__":
    if os.getenv("USE_MOCK_HW", "0") == "1":
        print("Using simulated hardware")
        initialize_simulated_hardware()
    main()
