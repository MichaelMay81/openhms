#!/bin/bash
# OpenHMS-800 Deployment Script
# Repository: https://github.com/MichaelMay81/openhms800

echo "Installing OpenHMS-800 service..."

# 1. Ensure uv is installed via pip
python3 -m pip install -U uv

# 2. Setup VENV and install from GitHub
uv venv
source .venv/bin/activate
uv pip install git+https://github.com/MichaelMay81/openhms800.git

# 3. Setup Systemd Service
CURRENT_DIR=$(pwd)
CURRENT_USER=$(whoami)

# Ensure the service template exists
if [ ! -f "openhms-800.service" ]; then
    echo "Service template not found locally. Fetching from GitHub..."
    curl -sSL https://raw.githubusercontent.com/MichaelMay81/openhms800/master/openhms-800.service -o openhms-800.service
fi

echo "Configuring systemd service for user $CURRENT_USER at $CURRENT_DIR..."

# Create a temporary service file with dynamic paths
sed "s|SEARCH_DIR|$CURRENT_DIR|g; s|SEARCH_USER|$CURRENT_USER|g" openhms-800.service > openhms-800.service.tmp

sudo cp openhms-800.service.tmp /etc/systemd/system/openhms-800.service
rm openhms-800.service.tmp

sudo systemctl daemon-reload
sudo systemctl enable openhms-800.service
sudo systemctl start openhms-800.service

echo "Deployment complete. Check status with: sudo systemctl status openhms-800"
