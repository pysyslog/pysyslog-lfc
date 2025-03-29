#!/bin/bash

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root"
    exit 1
fi

# Install system dependencies
if [ -f /etc/debian_version ]; then
    # Debian/Ubuntu
    apt update
    apt install -y python3 python3-pip python3-dev git
elif [ -f /etc/redhat-release ]; then
    # RHEL/CentOS
    yum install -y python3 python3-pip python3-devel git
elif [ -f /etc/arch-release ]; then
    # Arch Linux
    pacman -Syu --noconfirm python python-pip base-devel git
fi

# Create system user if it doesn't exist
if ! id "pysyslog" &>/dev/null; then
    useradd -r -s /bin/false pysyslog
fi

# Create configuration directories
mkdir -p /etc/pysyslog/conf.d

# Copy configuration files
cp etc/pysyslog/main.ini /etc/pysyslog/
cp etc/pysyslog/conf.d/*.ini /etc/pysyslog/conf.d/

# Set permissions
chown -R pysyslog:pysyslog /etc/pysyslog

# Install Python package
pip3 install .

# Install service
if [ -f /etc/debian_version ] || [ -f /etc/redhat-release ]; then
    # systemd
    cp etc/systemd/system/pysyslog.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable pysyslog
    systemctl start pysyslog
elif [ -f /etc/arch-release ]; then
    # systemd (Arch)
    cp etc/systemd/system/pysyslog.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable pysyslog
    systemctl start pysyslog
fi

echo "PySyslog LFC installed successfully!" 