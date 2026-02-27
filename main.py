import os
import time
import threading
from datetime import datetime

from adc import ADS124S08
from data_logger import DataLogger
import sensors
import config
from app import get_socketio, set_current_logger, get_restart_requested_event
from pi import get_system_info


def main():
    GPIOCHIP = "/dev/gpiochip0"  # Pi Zero/3/4; adjust if needed

    # Load settings from json file(sets config.LOAD_CELLS, etc., and ADC_*)
    config.load_settings()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(script_dir, "data")

    logger = DataLogger(base_dir=save_dir)
    set_current_logger(logger)

    # Get socketio instance for emitting data
    socketio = get_socketio()

    ADC1 = ADS124S08(id=1, spi_bus=0, spi_dev=0, gpiochip=GPIOCHIP, reset_pin=22, drdy_pin=27, start_pin=17, max_speed_hz=100_000)
    ADC2 = ADS124S08(id=2, spi_bus=0, spi_dev=1, gpiochip=GPIOCHIP, reset_pin=25, drdy_pin=24, start_pin=26, max_speed_hz=100_000)

    # Initialize sensor objects based on config
    sensor_labels, load_cells, pressure_transducers, rtds = sensors.initialize_sensors(ADC1, ADC2)

    # Track session start time for relative time
    session_start_time = None

    # Track last system info update time for throttling
    last_system_info_time = None
    system_info_interval = 2.5
    do_restart = False

    try:
        # Reset and basic config
        ADC1.hardware_reset()
        ADC2.hardware_reset()
        ADC1.configure_basic(use_internal_ref=False, gain=1, data_rate=config.ADC_DATARATE_CODE)
        ADC2.configure_basic(use_internal_ref=False, gain=1, data_rate=config.ADC_DATARATE_CODE)

        # Start conversions (continuous)
        ADC1.start()
        ADC2.start()

        while True:
            if get_restart_requested_event().is_set():
                break
            now = datetime.now()
            time_now_str = now.strftime("%H:%M:%S.%f")

            # Initialize session start time on first iteration
            if session_start_time is None:
                session_start_time = now

            # Read sensor values
            voltages, sensor_values = sensors.read_sensors(load_cells, pressure_transducers, rtds)
            row_data = [time_now_str] + voltages
            logger.log_row(row_data)
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
        do_restart = get_restart_requested_event().is_set()
        get_restart_requested_event().clear()
        ADC1.stop()
        ADC2.stop()
        ADC1.close()
        ADC2.close()
        set_current_logger(None)
    return "restart" if do_restart else None


if __name__ == "__main__":
    # Import app here to avoid circular import
    from app import app

    # Start Flask-SocketIO server in a separate thread
    socketio = get_socketio()
    # IMPORTANT: Werkzeug's debug reloader installs signal handlers, which is not allowed
    # outside the main thread. Since we run the server in a background thread, we must
    # disable the reloader (and effectively disable debug mode here).
    server_thread = threading.Thread(target=lambda: socketio.run(app, host="0.0.0.0", port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True), daemon=True)
    server_thread.start()

    time.sleep(3)

    # Run main data acquisition loop; re-run on restart request
    while True:
        result = main()
        if result != "restart":
            break
