import os
import time
import json
import threading
from flask import Flask, jsonify, request, send_from_directory
from daq_manager import DAQManager
from Enabled_Inputs import ADC1_CHANNELS, ADC2_CHANNELS

# --- Configuration ---
# Get the absolute path of the directory where this script is
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Set the data directory to be a 'data' folder in the same directory
DATA_DIR = os.path.join(BASE_DIR, "data")

# --- NEW: Define the path to your static folder ---
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Ensure the data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# --- App Initialization ---
app = Flask(__name__)
# Instantiate our new DAQ Manager
# We pass it the initial channel configurations
daq_manager = DAQManager(data_dir=DATA_DIR, initial_adc1_config=ADC1_CHANNELS, initial_adc2_config=ADC2_CHANNELS)

# --- API Endpoints ---


# --- MODIFIED: This route is now '/' ---
@app.route("/")
def serve_gui():
    """
    MODIFIED: Serves the main HTML GUI file.
    This file is expected to be in a 'static' folder.
    """
    try:
        # --- MODIFIED: This now sends the actual file ---
        return send_from_directory(STATIC_DIR, "index.html")
    except FileNotFoundError:
        return (
            "<h1>Error</h1><p>index.html not found.</p><p>Make sure you have a 'static' folder in the same directory as web_server.py, and index.html is inside it.</p>",
            404,
        )


@app.route("/api/status", methods=["GET"])
def get_status():
    """Returns the current status of the DAQ."""
    return jsonify(
        {"is_logging": daq_manager.is_logging(), "current_file": daq_manager.get_current_filename(), "message": daq_manager.get_status_message()}
    )


@app.route("/api/logging/start", methods=["POST"])
def start_logging():
    """Starts a new logging session."""
    if daq_manager.is_logging():
        return jsonify({"error": "Logging is already in progress"}), 400

    try:
        filename = daq_manager.start_logging()
        return jsonify({"message": "Logging started", "filename": filename}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to start logging: {str(e)}"}), 500


@app.route("/api/logging/stop", methods=["POST"])
def stop_logging():
    """Stops the current logging session."""
    if not daq_manager.is_logging():
        return jsonify({"error": "Logging is not in progress"}), 400

    try:
        filename = daq_manager.stop_logging()
        return jsonify({"message": "Logging stopped", "filename": filename})
    except Exception as e:
        return jsonify({"error": f"Failed to stop logging: {str(e)}"}), 500


@app.route("/api/channels", methods=["GET"])
def get_channels():
    """Gets the current channel configuration."""
    return jsonify(daq_manager.get_channel_config())


@app.route("/api/channels", methods=["POST"])
def set_channels():
    """
    Sets the channel configuration.
    This will only apply to the *next* logging session.
    Expects JSON data: {'adc1': {...}, 'adc2': {...}}
    """
    if daq_manager.is_logging():
        return jsonify({"error": "Cannot change channels while logging is active. Stop logging first."}), 400

    try:
        data = request.json
        if "adc1" not in data or "adc2" not in data:
            return jsonify({"error": 'POST data must include "adc1" and "adc2" keys.'}), 400

        daq_manager.set_channel_config(data["adc1"], data["adc2"])

        return jsonify({"message": 'Channel config updated. This will be used on the next "start".', "new_config": daq_manager.get_channel_config()})
    except Exception as e:
        return jsonify({"error": f"Failed to update config: {str(e)}"}), 500


# --- File Download Endpoint ---


@app.route("/data/<path:filename>", methods=["GET"])
def download_file(filename):
    """
    This is the "send file" feature.
    It allows a remote client to download any file from the DATA_DIR.
    Example: GET http://<pi_ip>:5000/data/DATA-2025-11-12_15-30-00.csv
    """
    try:
        return send_from_directory(DATA_DIR, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found."}), 404


# --- Main Execution ---

if __name__ == "__main__":
    print(f"Starting DAQ Web Server...")
    print(f"Data directory is: {DATA_DIR}")
    # --- NEW: Print path to static directory ---
    print(f"GUI directory is: {STATIC_DIR}")
    print(f"Access the GUI at http://<your_pi_ip>:5000")
    try:
        # Host '0.0.0.0' makes it accessible on your local network
        app.run(host="0.0.0.0", port=5000, debug=False)
    except Exception as e:
        print(f"Failed to start web server: {e}")
    finally:
        # Ensure we stop logging if the server crashes
        if daq_manager.is_logging():
            print("Web server shutting down. Stopping logging...")
            daq_manager.stop_logging()
