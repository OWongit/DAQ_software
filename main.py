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

# ANSI colour helpers
_RST = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GREEN = "\033[32m"
_CYAN = "\033[36m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_MAGENTA = "\033[35m"
_BLUE = "\033[34m"


def main():
    GPIOCHIP = "/dev/gpiochip0"

    config.load_settings()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(script_dir, "data")

    logger = DataLogger(base_dir=save_dir)
    set_current_logger(logger)

    socketio = get_socketio()

    ADC1 = ADS124S08(id=1, spi_bus=0, spi_dev=0, gpiochip=GPIOCHIP, reset_pin=22, drdy_pin=27, start_pin=17, max_speed_hz=100_000)
    ADC2 = ADS124S08(id=2, spi_bus=0, spi_dev=1, gpiochip=GPIOCHIP, reset_pin=25, drdy_pin=24, start_pin=26, max_speed_hz=100_000)

    sensor_labels, load_cells, pressure_transducers, rtds = sensors.initialize_sensors(ADC1, ADC2)

    n_lc = sum(1 for _, s in load_cells)
    n_pt = sum(1 for _, s in pressure_transducers)
    n_rtd = sum(1 for _, s in rtds)
    print(f"\n{_BOLD}{_CYAN}── DAQ Session ──{_RST}")
    print(f"  {_GREEN}Load cells  : {n_lc}{_RST}")
    print(f"  {_YELLOW}Pressure    : {n_pt}{_RST}")
    print(f"  {_MAGENTA}RTDs        : {n_rtd}{_RST}")
    print(f"  {_BLUE}Data rate   : code {config.ADC_DATARATE_CODE}{_RST}")
    print(f"  {_DIM}Log dir     : {save_dir}{_RST}\n")

    session_start_time = None
    last_system_info_time = None
    last_status_time = None
    system_info_interval = 2.5
    status_interval = 5.0
    sample_count = 0
    do_restart = False

    try:
        ADC1.hardware_reset()
        ADC2.hardware_reset()
        ADC1.configure_basic(use_internal_ref=False, gain=1, data_rate=config.ADC_DATARATE_CODE)
        ADC2.configure_basic(use_internal_ref=False, gain=1, data_rate=config.ADC_DATARATE_CODE)

        ADC1.start()
        ADC2.start()

        print(f"{_GREEN}{_BOLD}▶ Acquisition running{_RST}  (Ctrl-C to stop)\n")

        while True:
            if get_restart_requested_event().is_set():
                break
            now = datetime.now()
            time_now_str = now.strftime("%H:%M:%S.%f")

            if session_start_time is None:
                session_start_time = now

            csv_columns, sensor_values = sensors.read_sensors(load_cells, pressure_transducers, rtds)
            row_data = [time_now_str] + csv_columns
            logger.log_row(row_data)
            sample_count += 1

            relative_time = (now - session_start_time).total_seconds()

            socketio.emit("sensor_data", {"labels": sensor_labels, "time": relative_time, "values": sensor_values})

            if last_status_time is None or (now - last_status_time).total_seconds() >= status_interval:
                elapsed = relative_time
                rate = sample_count / elapsed if elapsed > 0 else 0
                parts = []
                idx = 0
                for name, _ in load_cells:
                    parts.append(f"{_GREEN}{name}={sensor_values[idx]:.2f}{_RST}")
                    idx += 1
                for name, _ in pressure_transducers:
                    parts.append(f"{_YELLOW}{name}={sensor_values[idx]:.2f}{_RST}")
                    idx += 1
                for name, _ in rtds:
                    parts.append(f"{_MAGENTA}{name}={sensor_values[idx]:.1f}°C{_RST}")
                    idx += 1
                vals = "  ".join(parts) if parts else f"{_DIM}no sensors{_RST}"
                print(
                    f"{_DIM}{now.strftime('%H:%M:%S')}{_RST}  "
                    f"{_CYAN}samples={sample_count}  {rate:.1f} S/s{_RST}  "
                    f"{vals}"
                )
                last_status_time = now

            if last_system_info_time is None or (now - last_system_info_time).total_seconds() >= system_info_interval:
                try:
                    system_info = get_system_info()
                    socketio.emit("system_info", system_info)
                    last_system_info_time = now
                except Exception as e:
                    print(f"{_RED}System info error: {e}{_RST}")

    except KeyboardInterrupt:
        print(f"\n{_YELLOW}{_BOLD}■ Stopped by user{_RST}")
    finally:
        do_restart = get_restart_requested_event().is_set()
        get_restart_requested_event().clear()
        ADC1.stop()
        ADC2.stop()
        ADC1.close()
        ADC2.close()
        set_current_logger(None)
        print(f"{_DIM}  Total samples: {sample_count}{_RST}\n")
    return "restart" if do_restart else None


if __name__ == "__main__":
    from app import app

    socketio = get_socketio()
    server_thread = threading.Thread(target=lambda: socketio.run(app, host="0.0.0.0", port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True), daemon=True)
    server_thread.start()

    print(f"\n{_BOLD}{_BLUE}DAQ Software starting…{_RST}")
    print(f"  {_DIM}Web UI → http://0.0.0.0:5000{_RST}\n")
    time.sleep(3)

    while True:
        result = main()
        if result != "restart":
            break
