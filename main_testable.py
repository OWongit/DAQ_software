import time

# --- Conditional Import ---
# This will import the "real" ADC class on a Pi,
# and the "testable" one (which uses mocks) on your PC.
try:
    from ADC import ADS124S08
    print("--- Main: Running on REAL hardware ---")
except (ImportError, ModuleNotFoundError):
    print("--- Main: (Mock Mode) Hardware not found, importing ADC_testable ---")
    from ADC_testable import ADS124S08
# --------------------------

from Enabled_Inputs import ADC1_CHANNELS, ADC2_CHANNELS


def main():
    # In mock mode, this path doesn't have to exist,
    # the mock library will just print it.
    GPIOCHIP = "/dev/gpiochip0"  

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
        # Limit to 3 loops for testing
        while run_count < 3: 
            print(f"---- Scan {run_count + 1}/3 ----")
            for label, (ch_idx, enabled) in ADC1_CHANNELS.items():
                if not enabled:
                    continue
                try:
                    code1, volts1 = adc1.read_voltage_single(ch_idx, vref=VREF, gain=GAIN, settle_discard=True)
                    print(f"ADC1 - {label}: {volts1:+.6f} V  (code={code1:+d})")
                except Exception as e:
                    print(f"Error reading ADC1 {label}: {e}")

            for label, (ch_idx, enabled) in ADC2_CHANNELS.items():
                if not enabled:
                    continue
                try:
                    code2, volts2 = adc2.read_voltage_single(ch_idx, vref=VREF, gain=GAIN, settle_discard=True)
                    print(f"ADC2 - {label}: {volts2:+.6f} V  (code={code2:+d})")
                except Exception as e:
                    print(f"Error reading ADC2 {label}: {e}")
            
            time.sleep(0.2)
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
