# DietPi Setup for OpenHMS

This guide outlines the secure, recommended procedure for deploying the OpenHMS application on a Raspberry Pi running DietPi.

## 1. Prerequisites
Ensure your system is updated and you have root/sudo access.

```bash
sudo apt update
sudo apt upgrade
```

## 2. Enable Bluetooth
On DietPi, Bluetooth is often disabled by default. Enable it directly:

```bash
sudo /boot/dietpi/func/dietpi-set_hardware bluetooth enable
```

## 3. Create a Secure System User
It is best practice to run services as a dedicated system user without login privileges.

```bash
# Create the system user
sudo adduser --system --group --no-create-home --shell /usr/sbin/nologin openhms

# Add the user to the 'bluetooth' group for hardware access
sudo usermod -aG bluetooth openhms
```

## 4. Prepare the Application Directory
Clone or place the application code in a secure, dedicated location.

```bash
# Create directory
sudo mkdir -p /opt/openhms
# Set ownership to the system user
sudo chown -R openhms:openhms /opt/openhms
```

## 5. Deploy the Application
To deploy the application, open a shell session as the `openhms` system user in the application directory, and follow the setup instructions provided in the project's README or official documentation.

```bash
# Open a shell as the openhms user in the app directory
sudo -u openhms bash -c 'cd /opt/openhms && bash'
```

Once in this shell, proceed with the standard setup steps for the OpenHMS application.

## 6. Verification
Verify the service is running correctly:

```bash
sudo systemctl status openhms
```

## Troubleshooting
*   **Memory/Swap:** If the build process for dependencies fails, increase your swap space: `dietpi-config` -> `Advanced Options` -> `Swapfile size`. Aim for at least 1.5GB total.
*   **Logs:** Monitor logs for troubleshooting:
    `sudo journalctl -u openhms -f`
