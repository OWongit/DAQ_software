import eventlet
eventlet.monkey_patch()

import os
import time
import threading
from datetime import datetime
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit

from ADC import ADS124S08
from data_logger import DataLogger
import sensors
import config
import ADC

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

thread = None
thread_lock = threading.Lock()
is_logging = False
logger = None
latest_file = None  # <--- NEW: Track the filename
script_dir = os.path.dirname(os.path.abspath(__file__))
save_dir = os.path.join(script_dir, "data")

# ... (Hardware Setup - initialize_hardware function remains the same) ...
def initialize_hardware():
    # Check for Mock Mode
    user_request_mock = os.getenv("USE_MOCK_HW", "0") == "1"
    auto_detected_mock = getattr(ADC, 'USE_MOCK_HW', False)
    
    if user_request_mock or auto_detected_mock:
        print("--- Using Simulated Hardware ---")
        import sims.mock_spidev as mock_spidev
        from sims.ads124s08_mock import MockADS124S08SpiDevice
        from sims.signal_generator import example_ran
        
        skip_ains = (3, 5, 6, 7)
        adc1_sources = {i: example_ran() for i in range(12) if i not in skip_ains}
        adc2_sources = {i: example_ran() for i in range(12) if i not in skip_ains}
        mock_spidev.register_device(0, 0, MockADS124S08SpiDevice(signal_sources=adc1_sources, v_ref=5))
        mock_spidev.register_device(0, 1, MockADS124S08SpiDevice(signal_sources=adc2_sources, v_ref=5))

    adc1 = ADS124S08(id=1, spi_bus=0, spi_dev=0, gpiochip="/dev/gpiochip0", reset_pin=17, drdy_pin=25, start_pin=27)
    adc2 = ADS124S08(id=2, spi_bus=0, spi_dev=1, gpiochip="/dev/gpiochip0", reset_pin=22, drdy_pin=24, start_pin=26)
    
    adc1.hardware_reset()
    adc2.hardware_reset()
    adc1.configure_basic(use_internal_ref=False, gain=1)
    adc2.configure_basic(use_internal_ref=False, gain=1)
    
    adc1.start()
    adc2.start()
    
    return adc1, adc2

sensor_labels, load_cells, pressure_transducers, rtds = sensors.initialize_sensors()

def background_thread():
    global is_logging, logger, latest_file
    print("Background thread started")
    adc1, adc2 = initialize_hardware()
    VREF = 5
    GAIN = 1

    while True:
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S.%f")[:-3]
        timestamp = time.time() * 1000

        v1 = adc1.read_voltage_full(vref=VREF, gain=GAIN)
        v2 = adc2.read_voltage_full(vref=VREF, gain=GAIN)
        voltages = v1 + v2
        
        sensor_values = sensors.read_sensors(voltages, load_cells, pressure_transducers, rtds)
        data_map = dict(zip(sensor_labels, sensor_values))
        
        # Emit data + filename info
        socketio.emit('daq_update', {
            'timestamp': timestamp,
            'sensors': data_map,
            'is_logging': is_logging,
            'filename': latest_file # <--- Send filename to client
        })

        if is_logging and logger:
            row = [time_str] + voltages
            logger.log_row(row)

        socketio.sleep(0.1)

@app.route('/')
def index():
    return render_template('index.html', sensor_labels=sensor_labels)

# --- NEW: Route to download files ---
@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(save_dir, filename, as_attachment=True)

@socketio.on('connect')
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)

@socketio.on('toggle_logging')
def handle_logging(data):
    global is_logging, logger, latest_file
    cmd = data.get('command')
    
    if cmd == 'start' and not is_logging:
        logger = DataLogger(base_dir=save_dir)
        latest_file = logger.get_filename() # <--- Capture filename
        # Write header to new file
        # Note: Using hardcoded header from data_logger.py for now,
        # but ideally this should match dynamic sensor list
        # header = ["timestamp"] + sensor_labels
        # logger.write_header(header) 
        
        is_logging = True
        print(f"Logging Started: {latest_file}")
        
    elif cmd == 'stop' and is_logging:
        is_logging = False
        if logger:
            logger.close()
            logger = None
        print("Logging Stopped")

if __name__ == '__main__':
    # Create data dir if it doesn't exist so send_from_directory doesn't crash
    os.makedirs(save_dir, exist_ok=True)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)