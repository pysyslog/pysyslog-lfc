#!/bin/bash

# Exit on error
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Check if service exists and stop/disable it
if systemctl list-unit-files | grep -q "pysyslog.service"; then
    echo "Stopping and disabling service..."
    systemctl stop pysyslog
    systemctl disable pysyslog
else
    echo "Service not found, skipping..."
fi

# Remove systemd service file if it exists
if [ -f /etc/systemd/system/pysyslog.service ]; then
    echo "Removing systemd service file..."
    rm -f /etc/systemd/system/pysyslog.service
else
    echo "Service file not found, skipping..."
fi

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

# Remove configuration and log directories if they exist
if [ -d /etc/pysyslog ]; then
    echo "Removing configuration directory..."
    rm -rf /etc/pysyslog
else
    echo "Configuration directory not found, skipping..."
fi

if [ -d /var/log/pysyslog ]; then
    echo "Removing log directory..."
    rm -rf /var/log/pysyslog
else
    echo "Log directory not found, skipping..."
fi

# Remove system user and group if they exist
if getent passwd pysyslog >/dev/null; then
    echo "Removing system user..."
    userdel pysyslog
else
    echo "System user not found, skipping..."
fi

if getent group pysyslog >/dev/null; then
    echo "Removing system group..."
    groupdel pysyslog
else
    echo "System group not found, skipping..."
fi

# Uninstall Python package
echo "Uninstalling Python package..."
pip3 uninstall -y pysyslog-lfc

echo "Uninstallation complete!" 