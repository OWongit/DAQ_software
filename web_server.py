import os
import time
import json
import threading
from flask import Flask, jsonify, request, send_from_directory
from daq_manager import DAQManager
from Enabled_Inputs import ADC1_CHANNELS, ADC2_CHANNELS

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
# --- FIX: Define the path to your static folder ---
STATIC_DIR = os.path.join(BASE_DIR, "static") 
os.makedirs(DATA_DIR, exist_ok=True)

# --- App Initialization ---
app = Flask(__name__)
daq_manager = DAQManager(
    data_dir=DATA_DIR,
    initial_adc1_config=ADC1_CHANNELS,
    initial_adc2_config=ADC2_CHANNELS
)

# --- API Endpoints ---

# --- FIX: This route is now '/' and serves the HTML file ---
@app.route('/')
def serve_gui():
    """Serves the main HTML GUI file from the 'static' folder."""
    try:
        return send_from_directory(STATIC_DIR, 'index.html')
    except FileNotFoundError:
        return "<h1>Error</h1><p>index.html not found.</p><p>Make sure you have a 'static' folder in the same directory as web_server.py, and index.html is inside it.</p>", 404

# --- NEW: Endpoint for live data ---
@app.route('/api/latest_data', methods=['GET'])
def get_latest_data():
    """Returns the most recent block of ADC readings."""
    return jsonify(daq_manager.get_latest_data())

@app.route('/api/status', methods=['GET'])
def get_status():
    """Returns the current status of the DAQ."""
    return jsonify({
        'is_logging': daq_manager.is_logging(),
        'current_file': daq_manager.get_current_filename(),
        'message': daq_manager.get_status_message()
    })

@app.route('/api/logging/start', methods=['POST'])
def start_logging():
    """Starts a new logging session."""
    if daq_manager.is_logging():
        return jsonify({'error': 'Logging is already in progress'}), 400
    try:
        filename = daq_manager.start_logging()
        return jsonify({'message': 'Logging started', 'filename': filename}), 201
    except Exception as e:
        return jsonify({'error': f'Failed to start logging: {str(e)}'}), 500

@app.route('/api/logging/stop', methods=['POST'])
def stop_logging():
    """Stops the current logging session."""
    if not daq_manager.is_logging():
        return jsonify({'error': 'Logging is not in progress'}), 400
    try:
        filename = daq_manager.stop_logging()
        return jsonify({'message': 'Logging stopped', 'filename': filename})
    except Exception as e:
        return jsonify({'error': f'Failed to stop logging: {str(e)}'}), 500

@app.route('/api/channels', methods=['GET'])
def get_channels():
    """Gets the current channel configuration."""
    return jsonify(daq_manager.get_channel_config())

@app.route('/api/channels', methods=['POST'])
def set_channels():
    """Sets the channel configuration."""
    if daq_manager.is_logging() or daq_manager._is_monitoring:
        return jsonify({'error': 'Cannot change channels while logging or monitoring is active.'}), 400
    try:
        data = request.json
        daq_manager.set_channel_config(data['adc1'], data['adc2'])
        return jsonify({'message': 'Channel config updated. This will be used on the next start.'})
    except Exception as e:
        return jsonify({'error': f'Failed to update config: {str(e)}'}), 500

# --- File Download Endpoint ---
@app.route('/data/<path:filename>', methods=['GET'])
def download_file(filename):
    """Allows a client to download any file from the DATA_DIR."""
    try:
        return send_from_directory(
            DATA_DIR,
            filename,
            as_attachment=True
        )
    except FileNotFoundError:
        return jsonify({'error': 'File not found.'}), 404

# --- Main Execution ---
if __name__ == '__main__':
    print(f"Starting DAQ Web Server...")
    print(f"Data directory is: {DATA_DIR}")
    print(f"GUI directory is: {STATIC_DIR}")
    print(f"Access the GUI at http://<your_ip_address>:5000")
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"Failed to start web server: {e}")
    finally:
        if daq_manager.is_logging():
            print("Web server shutting down. Stopping logging...")
            daq_manager.stop_logging()