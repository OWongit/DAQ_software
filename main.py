import os
import time
from datetime import datetime

from ADC import ADS124S08
from data_logger import DataLogger
from sensors import Load_Cell, Pressure_Transducer, RTD
import config

# if no raspberry pi use simulated hardware
USE_MOCK_HW = os.getenv("USE_MOCK_HW", "0") == "1"
if USE_MOCK_HW:
    import sims.mock_spidev as mock_spidev
    from sims.ads124s08_mock import MockADS124S08SpiDevice
    from sims.signal_generator import example_ran


def main():
    GPIOCHIP = "/dev/gpiochip0"  # Pi Zero/3/4; adjust if needed

    script_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(script_dir, "data")

    logger = DataLogger(base_dir=save_dir)

    # Initialize sensor objects based on config
    load_cells = []
    for name, cfg in config.LOAD_CELLS.items():
        if cfg['enabled']:
            sensor = Load_Cell(
                sig_plus_idx=cfg['sig_plus_idx'],
                sig_minus_idx=cfg['sig_minus_idx'],
                excitation_voltage=cfg['excitation_voltage'],
                sensitivity=cfg['sensitivity']
            )
            load_cells.append((name, sensor))

    pressure_transducers = []
    for name, cfg in config.PRESSURE_TRANSDUCERS.items():
        if cfg['enabled']:
            sensor = Pressure_Transducer(
                sig_idx=cfg['sig_idx'],
                excitation_voltage=cfg['excitation_voltage'],
                V_max=cfg['V_max'],
                V_min=cfg['V_min'],
                V_span=cfg['V_span'],
                P_min=cfg['P_min'],
                P_max=cfg['P_max']
            )
            pressure_transducers.append((name, sensor))

    rtds = []
    for name, cfg in config.RTDS.items():
        if cfg['enabled']:
            sensor = RTD(
                V_leg1_idx=cfg['V_leg1_idx'],
                V_leg2_idx=cfg['V_leg2_idx']
            )
            rtds.append((name, sensor))

    # if no raspberry pi use simulated hardware
    if USE_MOCK_HW:
        adc1_sources = {}
        for i in range(12):  # ain0 through ain11
            if i in (3, 5, 6, 7):  # skip ain3 and ain5 as IDAC lines
                continue
            adc1_sources[i] = example_ran()

        adc2_sources = {}
        for i in range(12):  # ain0 through ain11
            if i in (3, 5, 6, 7):  # skip ain3 and ain5 as IDAC lines
                continue
            adc2_sources[i] = example_ran()

        # Create the mock SPI-level ADC devices
        adc1_device = MockADS124S08SpiDevice(signal_sources=adc1_sources, v_ref=5)
        adc2_device = MockADS124S08SpiDevice(signal_sources=adc2_sources, v_ref=5)

        # Attach them to SPI bus 0, chip selects 0 and 1
        mock_spidev.register_device(0, 0, adc1_device)
        mock_spidev.register_device(0, 1, adc2_device)

    adc1 = ADS124S08(spi_bus=0, spi_dev=0, gpiochip=GPIOCHIP, reset_pin=17, drdy_pin=25, start_pin=27, max_speed_hz=1_000_000)
    adc2 = ADS124S08(spi_bus=0, spi_dev=1, gpiochip=GPIOCHIP, reset_pin=22, drdy_pin=24, start_pin=26, max_speed_hz=1_000_000)

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
            voltages = []
            now = datetime.now()
            time_now_str = now.strftime("%H:%M:%S.%f")

            for i in range(12):  # ain0 through ain11
                if i in (3, 5, 6, 7):  # skip ain3 and ain5 as IDAC lines
                    continue
                try:
                    _, volts1 = adc1.read_voltage_single(i, vref=VREF, gain=GAIN, settle_discard=True)
                    voltages.append(volts1)
                except Exception as e:
                    print(f"Error reading ADC1 AIN{i}: {e}")

            for i in range(12):  # ain0 through ain11
                if i in (3, 5, 6, 7):  # skip ain3 and ain5 as IDAC lines
                    continue
                try:
                    _, volts2 = adc2.read_voltage_single(i, vref=VREF, gain=GAIN, settle_discard=True)
                    voltages.append(volts2)
                except Exception as e:
                    print(f"Error reading ADC2 AIN{i}: {e}")

            # Log the raw float data (unchanged)
            row_data = [time_now_str] + voltages
            logger.log_row(row_data)
            time.sleep(0.1)

            # Read sensor values
            sensor_values = []
            sensor_labels = []
            
            # Read load cell values
            for name, sensor in load_cells:
                force = sensor.read(voltages)
                sensor_values.append(force)
                sensor_labels.append(f"{name}_Force")
            
            # Read pressure transducer values
            for name, sensor in pressure_transducers:
                pressure = sensor.read(voltages)
                sensor_values.append(pressure)
                sensor_labels.append(f"{name}_Pressure")
            
            # Read RTD values
            for name, sensor in rtds:
                temperature = sensor.read(voltages)
                sensor_values.append(temperature)
                sensor_labels.append(f"{name}_Temp")

            # Format for display: 4 sig figs (1.xxx → 3 decimal places)
            adc_str = ", ".join(f"{v:.3f}" for v in voltages)
            sensor_str = ", ".join(f"{v:.3f}" for v in sensor_values)

            print(f"{time_now_str} - Voltages: [{adc_str}]")
            print(f"{time_now_str} - Sensors: [{sensor_str}]")

    except KeyboardInterrupt:
        pass
    finally:
        adc1.stop()
        adc2.stop()
        adc1.close()
        adc2.close()


if __name__ == "__main__":
    main()
