#!/bin/bash
# OpenHMS: Phase 2 (Systemd Service Setup)
# To be run with sudo.

set -e

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)."
  exit 1
fi

echo "OpenHMS: Finalizing Systemd Service..."

# 1. Detect service environment
# We assume this script is run from the directory where Phase 1 was executed.
CURRENT_DIR=$(pwd)
SERVICE_USER=$(stat -c '%U' .)

if [ "$SERVICE_USER" == "root" ]; then
    echo "Warning: Current directory is owned by root."
    echo "It is recommended to run Phase 1 (setup_app.sh) as a non-privileged user."
    read -p "Continue using 'root' as the service user? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 2. Ensure the service template exists
if [ ! -f "openhms.service" ]; then
    echo "Service template not found locally. Fetching from GitHub..."
    curl -sSL https://raw.githubusercontent.com/MichaelMay81/openhms/master/openhms.service -o openhms.service
fi

# 3. Configure and install systemd service
echo "Configuring service for user $SERVICE_USER at $CURRENT_DIR..."

sed "s|SEARCH_DIR|$CURRENT_DIR|g; s|SEARCH_USER|$SERVICE_USER|g" openhms.service > openhms.service.tmp
cp openhms.service.tmp /etc/systemd/system/openhms.service
rm openhms.service.tmp

systemctl daemon-reload
systemctl enable openhms.service
systemctl start openhms.service

echo "Deployment complete."
echo "Check status with: systemctl status openhms"
