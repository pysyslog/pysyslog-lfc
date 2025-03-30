#!/bin/bash

# Exit on error
set -e

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a process is running
is_process_running() {
    pgrep -f "$1" >/dev/null
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Check if systemd is available
if ! command_exists systemctl; then
    echo "Error: systemd is not available"
    exit 1
fi

# Check if service exists and stop/disable it
if systemctl list-unit-files | grep -q "pysyslog.service"; then
    echo "Stopping and disabling service..."
    systemctl stop pysyslog || {
        echo "Warning: Failed to stop service, attempting to kill process..."
        if is_process_running "pysyslog"; then
            pkill -f "pysyslog" || {
                echo "Error: Failed to stop pysyslog process"
                exit 1
            }
        fi
    }
    systemctl disable pysyslog || {
        echo "Error: Failed to disable service"
        exit 1
    }
else
    echo "Service not found, skipping..."
fi

# Remove systemd service file if it exists
if [ -f /etc/systemd/system/pysyslog.service ]; then
    echo "Removing systemd service file..."
    rm -f /etc/systemd/system/pysyslog.service || {
        echo "Error: Failed to remove service file"
        exit 1
    }
else
    echo "Service file not found, skipping..."
fi

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload || {
    echo "Error: Failed to reload systemd"
    exit 1
}

# Backup configuration before removal
if [ -d /etc/pysyslog ]; then
    echo "Backing up configuration..."
    BACKUP_DIR="/etc/pysyslog.backup.$(date +%Y%m%d_%H%M%S)"
    cp -r /etc/pysyslog "$BACKUP_DIR" || {
        echo "Warning: Failed to backup configuration"
    }
fi

# Remove configuration and log directories if they exist
if [ -d /etc/pysyslog ]; then
    echo "Removing configuration directory..."
    rm -rf /etc/pysyslog || {
        echo "Error: Failed to remove configuration directory"
        exit 1
    }
else
    echo "Configuration directory not found, skipping..."
fi

if [ -d /var/log/pysyslog ]; then
    echo "Removing log directory..."
    rm -rf /var/log/pysyslog || {
        echo "Error: Failed to remove log directory"
        exit 1
    }
else
    echo "Log directory not found, skipping..."
fi

# Remove executable if it exists
if [ -f /usr/bin/pysyslog ]; then
    echo "Removing executable..."
    rm -f /usr/bin/pysyslog || {
        echo "Error: Failed to remove executable"
        exit 1
    }
else
    echo "Executable not found, skipping..."
fi

# Remove system user and group if they exist
if getent passwd pysyslog >/dev/null; then
    echo "Removing system user..."
    userdel pysyslog || {
        echo "Error: Failed to remove system user"
        exit 1
    }
else
    echo "System user not found, skipping..."
fi

if getent group pysyslog >/dev/null; then
    echo "Removing system group..."
    groupdel pysyslog || {
        echo "Error: Failed to remove system group"
        exit 1
    }
else
    echo "System group not found, skipping..."
fi

# Uninstall Python package
echo "Uninstalling Python package..."
pip3 uninstall -y pysyslog-lfc || {
    echo "Warning: Failed to uninstall Python package"
}

echo "Uninstallation complete!"
if [ -d "$BACKUP_DIR" ]; then
    echo "Configuration backup is available at: $BACKUP_DIR"
fi 