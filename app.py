"""
Flask-SocketIO server for real-time sensor data visualization.
"""

import os
from flask import Flask, send_from_directory, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__, static_folder="static")
app.config["SECRET_KEY"] = "daq-secret-key"
socketio = SocketIO(app, cors_allowed_origins="*")

# Global reference to current logger
current_logger = None


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
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    return send_from_directory(data_dir, filename, as_attachment=True)


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
