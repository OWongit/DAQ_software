#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ---------------------------------------------------------------------------
# Configurable: change this to use a different service/device name.
# Use lowercase with hyphens for SERVICE_NAME (e.g. daq, launch-controller) - no spaces.
# Optionally set DISPLAY_NAME for banner text (e.g. "Launch Controller").
# Updates the systemd service name, service file, and all systemctl commands.
#
# This script also:
#   - Creates a Python virtual environment (.venv)
#   - Installs all libraries from requirements.txt
#   - Configures the Raspberry Pi to run main.py on startup via systemd
# ---------------------------------------------------------------------------
SERVICE_NAME="${SERVICE_NAME:-daq}"
DISPLAY_NAME="${DISPLAY_NAME:-DAQ}"

# ANSI colors: purple for logo, gold for highlights
PURPLE='\033[35m'
GOLD='\033[33m'
RESET='\033[0m'

# Logo (purple)
echo -e "${PURPLE}"
echo "   @@@@@@@@@@@@@@@@          @@@@@@@@         @@@@@@@@@@@@@@@@     @@@@@@@@@@@@@@@@     
  @@@@@@@@@@@@@@@@@         @@@@@@@@@@        @@@@@@@@@@@@@@@@@@   @@@@@@@@@@@@@@@@@    
  @@@@                     @@@@@  @@@@@                     @@@@                @@@@    
  @@@@                     @@@@    @@@@                     @@@@                @@@@    
   @@@@@@@@@@@@@@@        @@@@      @@@@        @@@@@@@@@@@@@@@@     @@@@@@@@@@@@@@@    
     @@@@@@@@@@@@@@@     @@@@       @@@@@     @@@@@@@@@@@@@@@@     @@@@@@@@@@@@@@@      
                @@@@@   @@@@@        @@@@@    @@@@      @@@@       @@@@                 
                 @@@@  @@@@@          @@@@@   @@@@       @@@@@     @@@@                 
  @@@@@@@@@@@@@@@@@@   @@@@            @@@@   @@@@        @@@@@    @@@@                 
  @@@@@@@@@@@@@@@@    @@@@              @@@@  @@@@         @@@@@   @@@@"
echo -e "${RESET}"

BANNER="  ${DISPLAY_NAME} Software Installer (Raspberry Pi 5)"
SEP=$(printf '%*s' ${#BANNER} '' | tr ' ' '=')
echo -e "${GOLD}${SEP}${RESET}"
echo -e "${GOLD}${BANNER}${RESET}"
echo -e "${GOLD}${SEP}${RESET}"

# System packages required for SPI, GPIO, and Python venv support
echo ""
echo -e "${GOLD}[1/5] Installing system dependencies...${RESET}"
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
    echo -e "${GOLD}[2/5] Virtual environment already exists at $VENV_DIR, recreating...${RESET}"
    rm -rf "$VENV_DIR"
fi
echo ""
echo -e "${GOLD}[2/5] Creating virtual environment...${RESET}"
python3 -m venv "$VENV_DIR"

# Activate and install Python packages
echo ""
echo -e "${GOLD}[3/5] Installing Python dependencies...${RESET}"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt"

# Enable SPI interface if not already enabled
echo ""
echo -e "${GOLD}[4/5] Checking SPI interface...${RESET}"
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

# Fix line endings and make launcher executable
echo "  Preparing launcher script..."
sed -i 's/\r$//' "$SCRIPT_DIR/launcher.sh"
chmod +x "$SCRIPT_DIR/launcher.sh"

# Install systemd service for auto-start on boot
echo ""
echo -e "${GOLD}[5/5] Installing systemd service (auto-start on boot)...${RESET}"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=${SERVICE_NAME} Data Acquisition System
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
sudo systemctl enable "${SERVICE_NAME}.service"
echo "  ${SERVICE_NAME}.service installed and enabled."

echo ""
echo -e "${GOLD}=========================================${RESET}"
echo -e "${GOLD}  Installation complete!${RESET}"
echo -e "${GOLD}=========================================${RESET}"
echo ""
echo "  The ${DISPLAY_NAME} software will start automatically on boot."
echo ""
echo -e "${GOLD}  Useful commands:${RESET}"
echo "    sudo systemctl start ${SERVICE_NAME}      # Start now"
echo "    sudo systemctl stop ${SERVICE_NAME}       # Stop"
echo "    sudo systemctl restart ${SERVICE_NAME}    # Restart"
echo "    sudo systemctl status ${SERVICE_NAME}     # Check status"
echo "    journalctl -u ${SERVICE_NAME} -f          # View live logs"
echo ""
if [ "$SPI_CHANGED" = true ]; then
    echo "  NOTE: SPI was just enabled. A reboot is"
    echo "  required before the ${DISPLAY_NAME} can communicate"
    echo "  with the ADCs."
    echo ""
    read -p "  Reboot now? (y/N): " REBOOT_CHOICE
    if [ "$REBOOT_CHOICE" = "y" ] || [ "$REBOOT_CHOICE" = "Y" ]; then
        sudo reboot now
    fi
fi