import time
from Enabled_Inputs import ADC1_CHANNELS, ADC2_CHANNELS
from ADC import ADS124S08
import os
from data_logger import DataLogger


def main():
    GPIOCHIP = "/dev/gpiochip0"  # Pi Zero/3/4; adjust if needed

    script_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(script_dir, "data")
    
    logger = DataLogger(base_dir=save_dir)
    
    # --- Dynamically create headers based on Enabled_Inputs.py ---
    headers = ["timestamp_unix"]
    
    # Get all enabled channel labels for ADC1
    adc1_headers = [f"ADC1_{label}" for label, (_, enabled) in ADC1_CHANNELS.items() if enabled]
    # Get all enabled channel labels for ADC2
    adc2_headers = [f"ADC2_{label}" for label, (_, enabled) in ADC2_CHANNELS.items() if enabled]
    
    # Write the full header row
    logger.write_header(headers + adc1_headers + adc2_headers)

    adc1 = ADS124S08(spi_bus=0, spi_dev=0, gpiochip=GPIOCHIP, reset_pin=17, drdy_pin=25, start_pin=27, max_speed_hz=1_000_000)
    adc2 = ADS124S08(spi_bus=0, spi_dev=1, gpiochip=GPIOCHIP, reset_pin=22, drdy_pin=24, start_pin=26, max_speed_hz=1_000_000)

    try:
        # Reset and basic config
        adc1.hardware_reset()
        adc2.hardware_reset()
        adc1.configure_basic(use_internal_ref=True, gain=1)
        adc2.configure_basic(use_internal_ref=True, gain=1)

        # Start conversions (continuous)
        adc1.start()
        adc2.start()

        VREF = 2.5
        GAIN = 1

        while True:
            csv_timestamp = time.time()
            print_timestamp = time.strftime("%H:%M:%S", time.localtime(csv_timestamp))

            voltages1 = []
            voltages2 = []
            now = time.strftime("%H:%M:%S", time.localtime())

            print("------------- ADC 1 -------------")
            for label, (ch_idx, enabled) in ADC1_CHANNELS.items():
                if not enabled:
                    continue
                try:
                    _, volts1 = adc1.read_voltage_single(ch_idx, vref=VREF, gain=GAIN, settle_discard=True)
                    voltages1.append(volts1)
                except Exception as e:
                    print(f"Error reading ADC1 {label}: {e}")

            print("------------- ADC 2 -------------")
            for label, (ch_idx, enabled) in ADC2_CHANNELS.items():
                if not enabled:
                    continue
                try:
                    _, volts2 = adc2.read_voltage_single(ch_idx, vref=VREF, gain=GAIN, settle_discard=True)
                    voltages2.append(volts2)
                except Exception as e:
                    print(f"Error reading ADC2 {label}: {e}")
            
            # Log the data
            row_data = [csv_timestamp] + voltages1 + voltages2
            logger.log_row(row_data)
            time.sleep(0.2)

            print(f"{now} - ADC1: {voltages1}  ADC2: {voltages2}")

    except KeyboardInterrupt:
        pass
    finally:
        adc1.stop()
        adc2.stop()
        adc1.close()
        adc2.close()


if __name__ == "__main__":
    main()
