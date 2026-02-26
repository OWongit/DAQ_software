"""
Flask-SocketIO server for real-time sensor data visualization.
"""

import json
import os
import threading
from flask import Flask, send_from_directory, jsonify, request
from flask_socketio import SocketIO, emit

import config

#TODO: add rename feature in the settings. (displays )
#TODO: note that LC1 is 10V power, LC2 and LC3 are 5V power.
#TODO: Add offset setting
#TODO: Add unit selection N, Lb, KG setting


_script_dir = os.path.dirname(os.path.abspath(__file__))
_data_dir = os.path.join(_script_dir, "data")
_images_dir = os.path.join(_script_dir, "images")

app = Flask(__name__, static_folder="static")
app.config["SECRET_KEY"] = "daq-secret-key"
socketio = SocketIO(app, cors_allowed_origins="*")

# Global reference to current logger
current_logger = None

# Restart: main loop checks this and exits, then main() is run again
_restart_requested = threading.Event()


def request_restart():
    """Signal the main acquisition loop to exit and restart (re-run main())."""
    _restart_requested.set()


def get_restart_requested_event():
    """Return the Event so main.py can check and clear it."""
    return _restart_requested


@app.route("/")
def index():
    """Serve the main HTML page."""
    return send_from_directory("static", "index.html")


@app.route("/api/current-file")
def get_current_file():
    """Return the filename of the currently logging CSV file."""
    global current_logger
    if current_logger:
        filename = current_logger.get_filename()
        return jsonify({"filename": filename, "exists": True})
    return jsonify({"filename": None, "exists": False})


@app.route("/data/<filename>")
def download_file(filename):
    """Serve CSV files for download."""
    return send_from_directory(_data_dir, filename, as_attachment=True)


@app.route("/images/<path:filename>")
def serve_image(filename):
    """Serve images (favicon, logo, etc.) from the images folder."""
    return send_from_directory(_images_dir, filename)


@app.route("/api/settings", methods=["GET"])
def get_settings():
    """Return current sensor settings (editable fields only) for the UI."""
    return jsonify(config.get_editable_settings())


def _validate_settings_payload(data):
    """Validate POST /api/settings body; return (None, error_msg) or (payload, None)."""
    if not isinstance(data, dict):
        return None, "Body must be a JSON object"
    for key in ("load_cells", "pressure_transducers", "rtds"):
        if key not in data:
            return None, f"Missing key: {key}"
        if not isinstance(data[key], dict):
            return None, f"{key} must be an object"
    # Validate load_cells: enabled bool, sensitivity and max_load positive numbers, optional unit
    for name, cfg in data["load_cells"].items():
        if not isinstance(cfg, dict):
            return None, f"load_cells.{name} must be an object"
        if "enabled" in cfg and not isinstance(cfg["enabled"], bool):
            return None, f"load_cells.{name}.enabled must be boolean"
        if "unit" in cfg:
            if not isinstance(cfg["unit"], str) or cfg["unit"] not in config.LOAD_CELL_UNITS:
                return None, f"load_cells.{name}.unit must be one of: {sorted(config.LOAD_CELL_UNITS)}"
        if "sensitivity" in cfg:
            try:
                v = float(cfg["sensitivity"])
                if v <= 0:
                    return None, f"load_cells.{name}.sensitivity must be positive"
            except (TypeError, ValueError):
                return None, f"load_cells.{name}.sensitivity must be a number"
        if "max_load" in cfg:
            try:
                v = float(cfg["max_load"])
                if v < 0:
                    return None, f"load_cells.{name}.max_load must be non-negative"
            except (TypeError, ValueError):
                return None, f"load_cells.{name}.max_load must be a number"
        if "offset" in cfg:
            try:
                float(cfg["offset"])
            except (TypeError, ValueError):
                return None, f"load_cells.{name}.offset must be a number"
    # Validate pressure_transducers: enabled bool, P_min and P_max numbers
    for name, cfg in data["pressure_transducers"].items():
        if not isinstance(cfg, dict):
            return None, f"pressure_transducers.{name} must be an object"
        if "enabled" in cfg and not isinstance(cfg["enabled"], bool):
            return None, f"pressure_transducers.{name}.enabled must be boolean"
        if "unit" in cfg:
            if not isinstance(cfg["unit"], str) or cfg["unit"] not in config.PRESSURE_UNITS:
                return None, f"pressure_transducers.{name}.unit must be one of: {sorted(config.PRESSURE_UNITS)}"
        for k in ("P_min", "P_max"):
            if k in cfg:
                try:
                    float(cfg[k])
                except (TypeError, ValueError):
                    return None, f"pressure_transducers.{name}.{k} must be a number"
        if "offset" in cfg:
            try:
                float(cfg["offset"])
            except (TypeError, ValueError):
                return None, f"pressure_transducers.{name}.offset must be a number"
    # Validate rtds: enabled bool
    for name, cfg in data["rtds"].items():
        if not isinstance(cfg, dict):
            return None, f"rtds.{name} must be an object"
        if "enabled" in cfg and not isinstance(cfg["enabled"], bool):
            return None, f"rtds.{name}.enabled must be boolean"
        if "unit" in cfg:
            if not isinstance(cfg["unit"], str) or cfg["unit"] not in config.RTD_UNITS:
                return None, f"rtds.{name}.unit must be one of: {sorted(config.RTD_UNITS)}"
        if "offset" in cfg:
            try:
                float(cfg["offset"])
            except (TypeError, ValueError):
                return None, f"rtds.{name}.offset must be a number"
    # Validate optional adc: datarate_code 0-13, settle_discard bool
    if "adc" in data:
        adc = data["adc"]
        if not isinstance(adc, dict):
            return None, "adc must be an object"
        if "datarate_code" in adc:
            try:
                v = int(adc["datarate_code"])
                if v < 0 or v > 13:
                    return None, "adc.datarate_code must be between 0 and 13"
            except (TypeError, ValueError):
                return None, "adc.datarate_code must be an integer"
        if "settle_discard" in adc and not isinstance(adc["settle_discard"], bool):
            return None, "adc.settle_discard must be boolean"
    return data, None


@app.route("/api/settings", methods=["POST"])
def post_settings():
    """Save sensor settings (editable fields only) to settings.json."""
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    payload, err = _validate_settings_payload(data)
    if err:
        return jsonify({"error": err}), 400
    path = config.get_settings_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except OSError as e:
        return jsonify({"error": f"Failed to write settings: {e}"}), 500
    request_restart()
    return jsonify({"status": "saved"})


@socketio.on("connect")
def handle_connect():
    """Handle client connections."""
    print("Client connected")
    emit("connected", {"status": "connected"})


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnections."""
    print("Client disconnected")


def set_current_logger(logger):
    """Set the current logger instance."""
    global current_logger
    current_logger = logger


def get_socketio():
    """Get the socketio instance for use in main.py."""
    return socketio


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
