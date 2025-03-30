#!/bin/bash

# Exit on error
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Detect distribution
detect_distribution() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    else
        echo "unknown"
    fi
}

DISTRO=$(detect_distribution)

# Install required packages based on distribution
echo "Installing required packages..."
case $DISTRO in
    "rhel"|"centos"|"rocky")
        dnf install -y python3 python3-pip python3-devel systemd-devel python3-systemd gcc gcc-c++ make
        ;;
    "ubuntu"|"debian")
        apt-get update
        apt-get install -y python3 python3-pip python3-dev libsystemd-dev python3-systemd gcc g++ make
        ;;
    "suse"|"opensuse")
        zypper install -y python3 python3-pip python3-devel systemd-devel python3-systemd gcc gcc-c++ make
        ;;
    "alpine")
        apk add --no-cache python3 py3-pip python3-dev systemd-dev py3-systemd gcc g++ make
        ;;
    *)
        echo "Unsupported operating system: $DISTRO"
        exit 1
        ;;
esac

# Create system user and group if they don't exist
echo "Creating system user and group..."
if ! getent group pysyslog >/dev/null; then
    groupadd -r pysyslog
fi
if ! getent passwd pysyslog >/dev/null; then
    useradd -r -g pysyslog -s /sbin/nologin -d /var/lib/pysyslog pysyslog
fi

# Install the package
echo "Installing PySyslog LFC..."
pip3 install --system .

# Create necessary directories
echo "Creating system directories..."
mkdir -p /etc/pysyslog/conf.d
mkdir -p /var/log/pysyslog
mkdir -p /var/lib/pysyslog

# Set proper permissions
echo "Setting permissions..."
chown -R pysyslog:pysyslog /var/log/pysyslog
chown -R pysyslog:pysyslog /var/lib/pysyslog
chmod 755 /var/log/pysyslog
chmod 755 /var/lib/pysyslog

# Add pysyslog user to appropriate groups based on distribution
echo "Setting up user permissions..."
case $DISTRO in
    "ubuntu"|"debian")
        # Debian/Ubuntu use systemd-journal group
        usermod -a -G systemd-journal pysyslog
        ;;
    "rhel"|"centos"|"rocky"|"suse"|"opensuse")
        # RHEL/CentOS/SUSE use adm group
        usermod -a -G adm pysyslog
        ;;
    "alpine")
        # Alpine uses root group for log access
        usermod -a -G root pysyslog
        ;;
esac

# Copy configuration files
echo "Installing configuration..."
cp -r etc/pysyslog/* /etc/pysyslog/
chown -R pysyslog:pysyslog /etc/pysyslog
chmod 755 /etc/pysyslog
chmod 644 /etc/pysyslog/*.ini
chmod 644 /etc/pysyslog/conf.d/*.ini

# Create and update systemd service file
echo "Installing systemd service..."
cp etc/systemd/system/pysyslog.service /etc/systemd/system/
chmod 644 /etc/systemd/system/pysyslog.service

# Ensure the executable is in the system path
echo "Setting up executable..."
if [ -f /usr/local/bin/pysyslog ]; then
    cp /usr/local/bin/pysyslog /usr/bin/
    chmod 755 /usr/bin/pysyslog
    chown root:root /usr/bin/pysyslog
fi

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

# Enable and start service
echo "Enabling and starting service..."
systemctl enable pysyslog
systemctl start pysyslog

echo "Installation complete!"
echo "Main configuration file is located at /etc/pysyslog/main.ini"
echo "Additional configurations can be added in /etc/pysyslog/conf.d/"
echo "Logs are written to /var/log/pysyslog/" 