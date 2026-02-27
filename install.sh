#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================="
echo "  DAQ Software Installer (Raspberry Pi 5)"
echo "========================================="

# System packages required for SPI, GPIO, and Python venv support
echo ""
echo "[1/5] Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    libgpiod-dev \
    git

# Create virtual environment
VENV_DIR="$SCRIPT_DIR/.venv"
if [ -d "$VENV_DIR" ]; then
    echo ""
    echo "[2/5] Virtual environment already exists at $VENV_DIR, recreating..."
    rm -rf "$VENV_DIR"
fi
echo ""
echo "[2/5] Creating virtual environment..."
python3 -m venv "$VENV_DIR"

# Activate and install Python packages
echo ""
echo "[3/5] Installing Python dependencies..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt"

# Enable SPI interface if not already enabled
echo ""
echo "[4/5] Checking SPI interface..."
if ! grep -q "^dtparam=spi=on" /boot/firmware/config.txt 2>/dev/null && \
   ! grep -q "^dtparam=spi=on" /boot/config.txt 2>/dev/null; then
    echo "  Enabling SPI in boot config..."
    if [ -f /boot/firmware/config.txt ]; then
        echo "dtparam=spi=on" | sudo tee -a /boot/firmware/config.txt > /dev/null
    elif [ -f /boot/config.txt ]; then
        echo "dtparam=spi=on" | sudo tee -a /boot/config.txt > /dev/null
    fi
    SPI_CHANGED=true
else
    echo "  SPI is already enabled."
fi

# Create data directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/data"

# Make launcher executable
chmod +x "$SCRIPT_DIR/launcher.sh"

# Install systemd service for auto-start on boot
echo ""
echo "[5/5] Installing systemd service (auto-start on boot)..."
SERVICE_FILE="/etc/systemd/system/daq.service"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=DAQ Data Acquisition System
After=network.target

[Service]
Type=simple
ExecStart=$SCRIPT_DIR/launcher.sh
WorkingDirectory=$SCRIPT_DIR
Restart=on-failure
RestartSec=5
User=$(whoami)

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable daq.service
echo "  daq.service installed and enabled."

echo ""
echo "========================================="
echo "  Installation complete!"
echo "========================================="
echo ""
echo "  The DAQ software will start automatically on boot."
echo ""
echo "  Useful commands:"
echo "    sudo systemctl start daq      # Start now"
echo "    sudo systemctl stop daq       # Stop"
echo "    sudo systemctl restart daq    # Restart"
echo "    sudo systemctl status daq     # Check status"
echo "    journalctl -u daq -f          # View live logs"
echo ""
if [ "$SPI_CHANGED" = true ]; then
    echo "  NOTE: SPI was just enabled. A reboot is"
    echo "  required before the DAQ can communicate"
    echo "  with the ADCs."
    echo ""
    read -p "  Reboot now? (y/N): " REBOOT_CHOICE
    if [ "$REBOOT_CHOICE" = "y" ] || [ "$REBOOT_CHOICE" = "Y" ]; then
        sudo reboot now
    fi
fi
