import os
import time
import threading
from datetime import datetime

from ADC import ADS124S08
from data_logger import DataLogger
import sensors
from app import get_socketio, set_current_logger

get_system_info = None


# If using simulated hardware type: "export USE_MOCK_HW=1" in the terminal.
def initialize_simulated_hardware():
    global get_system_info
    import sims.mock_spidev as mock_spidev
    from sims.mock_pi_info import get_system_info as mock_get_system_info

    get_system_info = mock_get_system_info
    from sims.ads124s08_mock import MockADS124S08SpiDevice
    from sims.signal_generator import make_load_cell_signal_pair, make_pressure_transducer_signal, make_rtd_signal_pair

    # LS1_SIG-: AIN0, LS1_SIG+: AIN1, RTD1_L2: AIN2, RTD1_L1: AIN4, LS3_SIG-: AIN8, LS3_SIG+: AIN9, LS2_SIG-: AIN10, LS2_SIG+: AIN11, PT2_SIG: AIN0, PT1_SIG: AIN1, RTD2_L2: AIN2, RTD2_L1: AIN4, PT6_SIG: AIN8, PT5_SIG: AIN9, PT4_SIG: AIN10, PT3_SIG: AIN11
    adc1_sources = {}
    adc2_sources = {}
    adc1_sources[1], adc1_sources[0] = make_load_cell_signal_pair(max_load=907.1847, sensitivity=0.020, excitation_voltage=10.0)
    adc1_sources[4], adc1_sources[2] = make_rtd_signal_pair(
        T_min=-20.0, T_max=150.0, T0=0.0, R0=100.0, alpha=0.00385, I_exc=1e-3, lead_resistance=1.0
    )
    adc1_sources[9], adc1_sources[8] = make_load_cell_signal_pair(max_load=907.1847, sensitivity=0.020, excitation_voltage=5.0)
    adc1_sources[11], adc1_sources[10] = make_load_cell_signal_pair(max_load=907.1847, sensitivity=0.020, excitation_voltage=5.0)
    adc2_sources[0] = make_pressure_transducer_signal(P_min=0.0, P_max=100.0, excitation_voltage=5.0)
    adc2_sources[1] = make_pressure_transducer_signal(P_min=0.0, P_max=100.0, excitation_voltage=5.0)
    adc2_sources[4], adc2_sources[2] = make_rtd_signal_pair(
        T_min=-20.0, T_max=150.0, T0=0.0, R0=100.0, alpha=0.00385, I_exc=1e-3, lead_resistance=1.0
    )
    adc2_sources[8] = make_pressure_transducer_signal(P_min=0.0, P_max=100.0, excitation_voltage=5.0)
    adc2_sources[9] = make_pressure_transducer_signal(P_min=0.0, P_max=100.0, excitation_voltage=5.0)
    adc2_sources[10] = make_pressure_transducer_signal(P_min=0.0, P_max=100.0, excitation_voltage=5.0)
    adc2_sources[11] = make_pressure_transducer_signal(P_min=0.0, P_max=100.0, excitation_voltage=5.0)

    # Create the mock SPI-level ADC devices
    adc1_device = MockADS124S08SpiDevice(signal_sources=adc1_sources, v_ref=5)
    adc2_device = MockADS124S08SpiDevice(signal_sources=adc2_sources, v_ref=5)

    # Attach them to SPI bus 0, chip selects 0 and 1
    mock_spidev.register_device(0, 0, adc1_device)
    mock_spidev.register_device(0, 1, adc2_device)


def initialize_real_hardware():
    global get_system_info
    from pi_info import get_system_info as real_get_system_info

    get_system_info = real_get_system_info


def main():
    GPIOCHIP = "/dev/gpiochip0"  # Pi Zero/3/4; adjust if needed

    script_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(script_dir, "data")

    logger = DataLogger(base_dir=save_dir)
    set_current_logger(logger)

    # Get socketio instance for emitting data
    socketio = get_socketio()

    ADC1 = ADS124S08(id=1, spi_bus=0, spi_dev=0, gpiochip=GPIOCHIP, reset_pin=17, drdy_pin=25, start_pin=27, max_speed_hz=1_000_000)
    ADC2 = ADS124S08(id=2, spi_bus=0, spi_dev=1, gpiochip=GPIOCHIP, reset_pin=22, drdy_pin=24, start_pin=26, max_speed_hz=1_000_000)

    # Initialize sensor objects based on config
    sensor_labels, load_cells, pressure_transducers, rtds = sensors.initialize_sensors(ADC1, ADC2)

    # Track session start time for relative time
    session_start_time = None

    # Track last system info update time for throttling
    last_system_info_time = None
    system_info_interval = 2.5

    try:
        # Reset and basic config
        ADC1.hardware_reset()
        ADC2.hardware_reset()
        ADC1.configure_basic(use_internal_ref=False, gain=1)
        ADC2.configure_basic(use_internal_ref=False, gain=1)

        # Start conversions (continuous)
        ADC1.start()
        ADC2.start()

        VREF = 5
        GAIN = 1

        while True:
            now = datetime.now()
            time_now_str = now.strftime("%H:%M:%S.%f")

            # Initialize session start time on first iteration
            if session_start_time is None:
                session_start_time = now

            voltages1 = ADC1.read_voltage_full(vref=VREF, gain=GAIN)
            voltages2 = ADC2.read_voltage_full(vref=VREF, gain=GAIN)
            # [LS1_SIG-,LS1_SIG+,RTD1_L2,RTD1_L1,LS3_SIG-,LS3_SIG+,LS2_SIG-,LS2_SIG+,PT2_SIG,PT1_SIG,RTD2_L2,RTD2_L1,PT6_SIG,PT5_SIG,PT4_SIG,PT3_SIG]
            voltages = voltages1 + voltages2
            # Log the raw float data (unchanged)
            row_data = [time_now_str] + voltages
            logger.log_row(row_data)
            time.sleep(0.1)

            # Read sensor values
            sensor_values = sensors.read_sensors(load_cells, pressure_transducers, rtds)
            print(f"{time_now_str} - Voltages: {voltages}")

            # Calculate relative time in seconds from session start
            relative_time = (now - session_start_time).total_seconds()

            # Emit sensor data via SocketIO
            socketio.emit("sensor_data", {"labels": sensor_labels, "time": relative_time, "values": sensor_values})

            # Collect and emit system info every 2-3 seconds
            if last_system_info_time is None or (now - last_system_info_time).total_seconds() >= system_info_interval:
                try:
                    system_info = get_system_info()
                    socketio.emit("system_info", system_info)
                    last_system_info_time = now
                except Exception as e:
                    print(f"Error collecting system info: {e}")

    except KeyboardInterrupt:
        pass
    finally:
        ADC1.stop()
        ADC2.stop()
        ADC1.close()
        ADC2.close()
        set_current_logger(None)


if __name__ == "__main__":
    if os.getenv("USE_MOCK_HW", "0") == "1":
        print("Using simulated hardware")
        initialize_simulated_hardware()
    else:
        print("Using real hardware")
        initialize_real_hardware()

    # Import app here to avoid circular import
    from app import app

    # Start Flask-SocketIO server in a separate thread
    socketio = get_socketio()
    server_thread = threading.Thread(
        target=lambda: socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True), daemon=True
    )
    server_thread.start()

    # Run main data acquisition loop
    main()
