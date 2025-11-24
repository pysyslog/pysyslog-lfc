# Ubuntu Deployment Guide

This guide provides step-by-step instructions for deploying PySyslog LFC on Ubuntu.

## Quick Test (No Installation)

Test the application without installing it system-wide:

```bash
# 1. Clone the repository
git clone https://github.com/pysyslog/pysyslog-lfc.git
cd pysyslog-lfc

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install in development mode
pip install -e .

# 4. Run the test script
python3 test_example_config.py

# 5. Test with example configuration
python3 -m pysyslog -c etc/pysyslog/main.ini.example --log-level DEBUG
```

## Full System Installation

### Step 1: Install Prerequisites

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-dev git
```

### Step 2: Clone Repository

```bash
git clone https://github.com/pysyslog/pysyslog-lfc.git
cd pysyslog-lfc
```

### Step 3: Run Installation Script

```bash
sudo ./install.sh
```

The installation script will:
- Install required system packages
- Create system user `pysyslog`
- Install the Python package
- Set up configuration files in `/etc/pysyslog/`
- Create log directory `/var/log/pysyslog/`
- Install and start systemd service

### Step 4: Configure for Testing

The default `main.ini` references components that aren't implemented yet. Use the example config for testing:

```bash
# Backup original config
sudo cp /etc/pysyslog/main.ini /etc/pysyslog/main.ini.original

# Use working example config
sudo cp etc/pysyslog/main.ini.example /etc/pysyslog/main.ini

# Restart the service
sudo systemctl restart pysyslog
```

### Step 5: Verify Installation

```bash
# Check service status
sudo systemctl status pysyslog

# View service logs
sudo journalctl -u pysyslog -f

# Test the executable
/usr/bin/pysyslog --help
```

## Service Management

```bash
# Start the service
sudo systemctl start pysyslog

# Stop the service
sudo systemctl stop pysyslog

# Restart the service
sudo systemctl restart pysyslog

# Check status
sudo systemctl status pysyslog

# Enable auto-start on boot
sudo systemctl enable pysyslog

# Disable auto-start
sudo systemctl disable pysyslog
```

## Viewing Logs

```bash
# View systemd service logs
sudo journalctl -u pysyslog -f

# View last 50 lines
sudo journalctl -u pysyslog -n 50

# View logs since boot
sudo journalctl -u pysyslog -b

# View application logs (if configured to write files)
sudo tail -f /var/log/pysyslog/*.log
```

## Configuration Files

- **Main config**: `/etc/pysyslog/main.ini`
- **Additional configs**: `/etc/pysyslog/conf.d/*.ini`
- **Example config**: `etc/pysyslog/main.ini.example` (in repository)

## Testing the Configuration

Before deploying, test your configuration:

```bash
# Test configuration syntax
python3 -c "
import sys
sys.path.insert(0, 'src')
from pysyslog.config import ConfigLoader
loader = ConfigLoader()
config = loader.load('/etc/pysyslog/main.ini')
print(f'✓ Configuration valid: {len(config.flows)} flows loaded')
"

# Test manually (as pysyslog user)
sudo -u pysyslog /usr/bin/pysyslog -c /etc/pysyslog/main.ini --log-level DEBUG
```

## Troubleshooting

### Service won't start

1. **Check service logs:**
   ```bash
   sudo journalctl -u pysyslog -n 100
   ```

2. **Check configuration:**
   ```bash
   sudo -u pysyslog /usr/bin/pysyslog -c /etc/pysyslog/main.ini --log-level DEBUG
   ```

3. **Check permissions:**
   ```bash
   ls -la /etc/pysyslog/
   ls -la /var/log/pysyslog/
   ```

### Configuration errors

1. **Verify config syntax:**
   ```bash
   python3 -c "
   import sys
   sys.path.insert(0, 'src')
   from pysyslog.config import ConfigLoader
   try:
       ConfigLoader().load('/etc/pysyslog/main.ini')
       print('✓ Configuration is valid')
   except Exception as e:
       print(f'✗ Configuration error: {e}')
   "
   ```

2. **Check for missing components:**
   - See [MISSING_COMPONENTS.md](MISSING_COMPONENTS.md)
   - Use `main.ini.example` which only uses implemented components

### Permission issues

```bash
# Fix configuration permissions
sudo chown -R pysyslog:pysyslog /etc/pysyslog
sudo chmod 755 /etc/pysyslog
sudo chmod 644 /etc/pysyslog/*.ini

# Fix log directory permissions
sudo chown -R pysyslog:pysyslog /var/log/pysyslog
sudo chmod 755 /var/log/pysyslog
```

## Uninstallation

To remove PySyslog LFC:

```bash
cd pysyslog-lfc
sudo ./uninstall.sh
```

This will:
- Stop and disable the service
- Remove configuration files (backed up first)
- Remove the Python package
- Remove system user and group

## Next Steps

1. **Customize configuration**: Edit `/etc/pysyslog/main.ini` for your needs
2. **Add custom flows**: Create files in `/etc/pysyslog/conf.d/`
3. **Implement missing components**: See [MISSING_COMPONENTS.md](MISSING_COMPONENTS.md)
4. **Monitor logs**: Set up log rotation and monitoring

## Available Components

Currently implemented components you can use:
- **Inputs**: `memory`
- **Parsers**: `json`, `text`
- **Filters**: `field`
- **Outputs**: `stdout`, `memory`
- **Formats**: `json`, `text`

See the example configuration for usage examples.

