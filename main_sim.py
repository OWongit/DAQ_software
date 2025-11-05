import time
import os
from data_logger import DataLogger

# --- Conditional Import ---
# This will import the "real" ADC class on a Pi,
# and the "testable" one (which uses mocks) on your PC.
try:
    from ADC import ADS124S08

    print("--- Main: Running on REAL hardware ---")
except (ImportError, ModuleNotFoundError):
    print("--- Main: (Mock Mode) Hardware not found, importing ADC_testable ---")
    from sims.ADC_testable import ADS124S08
# --------------------------

from Enabled_Inputs import ADC1_CHANNELS, ADC2_CHANNELS


def main():
    # In mock mode, this path doesn't have to exist,
    # the mock library will just print it.
    GPIOCHIP = "/dev/gpiochip0"

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

        run_count = 0
        max_run_count = 50
        # Limit to 3 loops for testing
        while run_count < max_run_count:
            csv_timestamp = time.time()
            print_timestamp = time.strftime("%H:%M:%S", time.localtime(csv_timestamp))

            voltages1 = []
            voltages2 = []
            now = time.strftime("%H:%M:%S", time.localtime())

            for label, (ch_idx, enabled) in ADC1_CHANNELS.items():
                if not enabled:
                    continue
                try:
                    _, volts1 = adc1.read_voltage_single(ch_idx, vref=VREF, gain=GAIN, settle_discard=True)
                    voltages1.append(volts1)
                except Exception as e:
                    print(f"Error reading ADC1 {label}: {e}")

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
            
            # format: sign + 1 digit + '.' + 3 decimals  -> total 6 chars, e.g. "+1.234", "-0.567"
            fmt = "{:+.3f}"

            adc1_str = "[" + ", ".join(fmt.format(v) for v in voltages1) + "]"
            adc2_str = "[" + ", ".join(fmt.format(v) for v in voltages2) + "]"

            print(f"{now} - ADC1: {adc1_str}  ADC2: {adc2_str}")

            time.sleep(0.1)
            run_count += 1

    except KeyboardInterrupt:
        pass
    finally:
        print("\nShutting down...")
        adc1.stop()
        adc2.stop()
        adc1.close()
        adc2.close()
        print("Done.")


if __name__ == "__main__":
    main()
