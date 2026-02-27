# DAQ Software

Multi-ADC data acquisition system running on a Raspberry Pi 5 — Society for Advanced Rocket Propulsion (SARP) UW.

Reads load cells, pressure transducers, and RTDs via dual ADS124S08 ADCs over SPI. Streams live sensor data to a web-based GUI over Socket.IO and logs all readings to CSV.

![DAQ GUI](images/GUI_recording.gif)

## Features

- Real-time sensor graphs in the browser
- Configurable sensor parameters (enabled, sensitivity, units, offsets, etc.)
- Upload / download config files (see example_config.json)
- ADC data rate and settle-discard control
- CSV data logging with per-session files
- System info display (CPU temp, RAM, disk)
- Remote Raspberry Pi reboot from the web UI

## Installation

Clone the repository onto the Pi and run the install script:

```bash
git clone https://github.com/OWongit/DAQ_software
cd DAQ_software
chmod +x install.sh
./install.sh
```

The install script will:

1. Install system dependencies (`python3`, `python3-venv`, `libgpiod-dev`, etc.)
2. Create a Python virtual environment (`.venv`)
3. Install Python packages from `requirements.txt`
4. Enable the SPI interface if needed
5. Install and enable a systemd service (`daq.service`) so the DAQ starts automatically on boot

## Usage

After installation the DAQ starts automatically on boot. Open a browser and navigate to `http://<pi-ip>:5000`.

### Service Commands

```bash
sudo systemctl start daq       # Start the DAQ now
sudo systemctl stop daq        # Stop the DAQ
sudo systemctl restart daq     # Restart the DAQ
sudo systemctl status daq      # Check if it's running
journalctl -u daq -f           # Watch live log output
```

## Project Structure

```
DAQ_software/
├── main.py            # Entry point — acquisition loop and server startup
├── app.py             # Flask-SocketIO web server and API routes
├── config.py          # Sensor and ADC configuration (hardcoded + in-memory)
├── sensors.py         # Sensor classes and initialization
├── ADC.py             # ADS124S08 SPI driver
├── data_logger.py     # CSV logging
├── pi.py              # Raspberry Pi system info and reboot
├── settings.json      # Reference config file (not used at runtime)
├── install.sh         # Installation script
├── launcher.sh        # Launch script used by systemd service
├── requirements.txt   # Python dependencies
├── static/
│   └── index.html     # Web GUI (single-page app)
├── images/            # Favicon, logos
└── data/              # CSV log files (created at runtime)
```

## License

SARP — University of Washington
