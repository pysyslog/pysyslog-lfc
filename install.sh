#!/bin/bash

# Exit on error
set -e

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check disk space (in MB)
check_disk_space() {
    local required=$1
    local available=$(df -m /usr | awk 'NR==2 {print $4}')
    if [ "$available" -lt "$required" ]; then
        echo "Error: Insufficient disk space. Required: ${required}MB, Available: ${available}MB"
        exit 1
    fi
}

# Function to backup file if it exists
backup_file() {
    local file=$1
    if [ -f "$file" ]; then
        cp "$file" "${file}.bak"
        echo "Backed up $file to ${file}.bak"
    fi
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Check Python version
if ! command_exists python3; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$PYTHON_VERSION < 3.8" | bc -l) )); then
    echo "Error: Python 3.8 or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

# Check for required disk space (at least 100MB)
check_disk_space 100

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
        if ! command_exists dnf; then
            echo "Error: dnf is not available"
            exit 1
        fi
        dnf install -y python3 python3-pip python3-devel systemd-devel python3-systemd gcc gcc-c++ make || {
            echo "Error: Failed to install required packages"
            exit 1
        }
        ;;
    "ubuntu"|"debian")
        if ! command_exists apt-get; then
            echo "Error: apt-get is not available"
            exit 1
        fi
        apt-get update || {
            echo "Error: Failed to update package lists"
            exit 1
        }
        apt-get install -y python3 python3-pip python3-dev libsystemd-dev python3-systemd gcc g++ make || {
            echo "Error: Failed to install required packages"
            exit 1
        }
        ;;
    "suse"|"opensuse")
        if ! command_exists zypper; then
            echo "Error: zypper is not available"
            exit 1
        fi
        zypper install -y python3 python3-pip python3-devel systemd-devel python3-systemd gcc gcc-c++ make || {
            echo "Error: Failed to install required packages"
            exit 1
        }
        ;;
    "alpine")
        if ! command_exists apk; then
            echo "Error: apk is not available"
            exit 1
        fi
        apk add --no-cache python3 py3-pip python3-dev systemd-dev py3-systemd gcc g++ make || {
            echo "Error: Failed to install required packages"
            exit 1
        }
        ;;
    *)
        echo "Unsupported operating system: $DISTRO"
        exit 1
        ;;
esac

# Create system user and group if they don't exist
echo "Creating system user and group..."
if ! getent group pysyslog >/dev/null; then
    groupadd -r pysyslog || {
        echo "Error: Failed to create pysyslog group"
        exit 1
    }
fi
if ! getent passwd pysyslog >/dev/null; then
    useradd -r -g pysyslog -s /sbin/nologin -d /var/lib/pysyslog pysyslog || {
        echo "Error: Failed to create pysyslog user"
        exit 1
    }
fi

# Backup existing configuration if it exists
if [ -d "/etc/pysyslog" ]; then
    echo "Backing up existing configuration..."
    backup_file "/etc/pysyslog/main.ini"
    for conf in /etc/pysyslog/conf.d/*.ini; do
        if [ -f "$conf" ]; then
            backup_file "$conf"
        fi
    done
fi

# Install the package
echo "Installing PySyslog LFC..."
pip3 install --prefix=/usr . || {
    echo "Error: Failed to install PySyslog LFC"
    exit 1
}

# Create necessary directories
echo "Creating system directories..."
mkdir -p /etc/pysyslog/conf.d || {
    echo "Error: Failed to create configuration directory"
    exit 1
}
mkdir -p /var/log/pysyslog || {
    echo "Error: Failed to create log directory"
    exit 1
}
mkdir -p /var/lib/pysyslog || {
    echo "Error: Failed to create data directory"
    exit 1
}

# Set proper permissions
echo "Setting permissions..."
chown -R pysyslog:pysyslog /var/log/pysyslog || {
    echo "Error: Failed to set log directory permissions"
    exit 1
}
chown -R pysyslog:pysyslog /var/lib/pysyslog || {
    echo "Error: Failed to set data directory permissions"
    exit 1
}
chmod 755 /var/log/pysyslog || {
    echo "Error: Failed to set log directory mode"
    exit 1
}
chmod 755 /var/lib/pysyslog || {
    echo "Error: Failed to set data directory mode"
    exit 1
}

# Add pysyslog user to appropriate groups based on distribution
echo "Setting up user permissions..."
case $DISTRO in
    "ubuntu"|"debian")
        # Debian/Ubuntu use systemd-journal group
        usermod -a -G systemd-journal pysyslog || {
            echo "Error: Failed to add pysyslog to systemd-journal group"
            exit 1
        }
        ;;
    "rhel"|"centos"|"rocky"|"suse"|"opensuse")
        # RHEL/CentOS/SUSE use adm group
        usermod -a -G adm pysyslog || {
            echo "Error: Failed to add pysyslog to adm group"
            exit 1
        }
        ;;
    "alpine")
        # Alpine uses root group for log access
        usermod -a -G root pysyslog || {
            echo "Error: Failed to add pysyslog to root group"
            exit 1
        }
        ;;
esac

# Copy configuration files
echo "Installing configuration..."
cp -r etc/pysyslog/* /etc/pysyslog/ || {
    echo "Error: Failed to copy configuration files"
    exit 1
}
chown -R pysyslog:pysyslog /etc/pysyslog || {
    echo "Error: Failed to set configuration ownership"
    exit 1
}
chmod 755 /etc/pysyslog || {
    echo "Error: Failed to set configuration directory mode"
    exit 1
}
chmod 644 /etc/pysyslog/*.ini || {
    echo "Error: Failed to set configuration file modes"
    exit 1
}
chmod 644 /etc/pysyslog/conf.d/*.ini || {
    echo "Error: Failed to set configuration file modes"
    exit 1
}

# Create and update systemd service file
echo "Installing systemd service..."
backup_file "/etc/systemd/system/pysyslog.service"
cp etc/systemd/system/pysyslog.service /etc/systemd/system/ || {
    echo "Error: Failed to copy systemd service file"
    exit 1
}
chmod 644 /etc/systemd/system/pysyslog.service || {
    echo "Error: Failed to set service file mode"
    exit 1
}

# Ensure the executable is in the system path
echo "Setting up executable..."
if [ -f /usr/bin/pysyslog ]; then
    chmod 755 /usr/bin/pysyslog || {
        echo "Error: Failed to set executable mode"
        exit 1
    }
    chown root:root /usr/bin/pysyslog || {
        echo "Error: Failed to set executable ownership"
        exit 1
    }
else
    echo "Error: pysyslog executable not found in /usr/bin/"
    echo "Please check if the installation was successful"
    exit 1
fi

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload || {
    echo "Error: Failed to reload systemd"
    exit 1
}

# Enable and start service
echo "Enabling and starting service..."
systemctl enable pysyslog || {
    echo "Error: Failed to enable pysyslog service"
    exit 1
}
systemctl start pysyslog || {
    echo "Error: Failed to start pysyslog service"
    exit 1
}

echo "Installation complete!"
echo "Main configuration file is located at /etc/pysyslog/main.ini"
echo "Additional configurations can be added in /etc/pysyslog/conf.d/"
echo "Logs are written to /var/log/pysyslog/" 