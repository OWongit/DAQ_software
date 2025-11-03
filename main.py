import time
from Enabled_Inputs import ADC1_CHANNELS, ADC2_CHANNELS
from ADC import ADS124S08


def main():
    GPIOCHIP = "/dev/gpiochip0"  # Pi Zero/3/4; adjust if needed

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
            print("------------- ADC 1 -------------")
            for label, (ch_idx, enabled) in ADC1_CHANNELS.items():
                if not enabled:
                    continue
                try:
                    code1, volts1 = adc1.read_voltage_single(ch_idx, vref=VREF, gain=GAIN, settle_discard=True)
                    print(f"{label}: {volts1:+.6f} V  (code={code1:+d})")
                except Exception as e:
                    print(f"Error reading ADC1 {label}: {e}")

            print("------------- ADC 2 -------------")
            for label, (ch_idx, enabled) in ADC2_CHANNELS.items():
                if not enabled:
                    continue
                try:
                    code2, volts2 = adc2.read_voltage_single(ch_idx, vref=VREF, gain=GAIN, settle_discard=True)
                    print(f"{label}: {volts2:+.6f} V  (code={code2:+d})")
                except Exception as e:
                    print(f"Error reading ADC2 {label}: {e}")
            time.sleep(0.2)

    except KeyboardInterrupt:
        pass
    finally:
        adc1.stop()
        adc2.stop()
        adc1.close()
        adc2.close()


if __name__ == "__main__":
    main()
