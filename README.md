# OpenHMS-800 Unified Service

A lightweight, asynchronous service for monitoring Hoymiles HMS-800-2WB microinverters via Bluetooth Low Energy (BLE).

[![GitHub](https://img.shields.io/badge/GitHub-openhms800-blue?logo=github)](https://github.com/MichaelMay81/openhms800)

## Features
- **Real-time Monitoring:** Multi-channel PV and AC grid metrics.
- **Web Interface:** OpenDTU-inspired dashboard using `aiohttp` and `HTMX`.
- **Diagnostics:** Integrated system console and Raspberry Pi health monitoring.
- **Robust:** Automatic reconnection and persistent configuration.

## Installation
The service is designed for deployment on a Raspberry Pi. You can install it by downloading and running the deployment script:

```bash
mkdir openhms800 && cd openhms800
curl -sSL https://raw.githubusercontent.com/MichaelMay81/openhms800/master/deploy.sh -o deploy.sh
chmod +x deploy.sh
./deploy.sh
```

The script will:
1. Install `uv` if missing.
2. Create a virtual environment.
3. Install the `openhms800` service and `hms800-ble` library from GitHub.
4. Fetch and configure the systemd service with dynamic paths.

## Configuration
Settings are managed in `config.json` (created in the installation directory). You can modify these via the **Settings** tab in the Web UI, which also includes a button to restart the service to apply changes.

## Architecture
1. **BLE Layer:** Polls the inverter for raw metrics.
2. **State Layer:** Normalizes and stores data in a structured, thread-safe container.
3. **Web/MQTT Layer:** Serves the UI and forwards metrics to your broker.
