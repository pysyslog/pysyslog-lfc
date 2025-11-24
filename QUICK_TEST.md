# Quick Test Guide

## Development Mode Testing (No Sudo Required)

You've already completed steps 1-2! Here's how to test:

### Step 1: Verify Installation ✓
```bash
# You've already done this:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Step 2: Run Tests ✓
```bash
# Run the test script
python3 test_example_config.py
```

Expected output:
```
Testing demo flow...
✓ Demo flow processed 2 messages
Testing filtered flow...
✓ Filtered flow processed 1 message(s)
Testing reliable flow with channel...
✓ Reliable flow processed 2 messages
✓ All tests passed!
```

### Step 3: Test Manually
```bash
# Run with example configuration
# This will run in foreground - press Ctrl+C to stop
python3 -m pysyslog -c etc/pysyslog/main.ini.example --log-level DEBUG
```

## Important: Development vs System Installation

### Development Mode (What You're Using Now)
- ✅ No sudo required
- ✅ Uses config files from repository (`etc/pysyslog/main.ini.example`)
- ✅ Runs in your terminal
- ✅ Perfect for testing and development
- ❌ No systemd service
- ❌ No `/etc/pysyslog/` directory

### System Installation (Requires Sudo)
- ✅ Runs as system service
- ✅ Uses `/etc/pysyslog/main.ini`
- ✅ Starts automatically on boot
- ❌ Requires sudo/root access
- ❌ Requires running `sudo ./install.sh`

## Common Commands

### Development Mode
```bash
# Test the application
python3 test_example_config.py

# Run manually
python3 -m pysyslog -c etc/pysyslog/main.ini.example --log-level DEBUG

# Test configuration loading
python3 -c "
import sys
sys.path.insert(0, 'src')
from pysyslog.config import ConfigLoader
config = ConfigLoader().load('etc/pysyslog/main.ini.example')
print(f'Loaded {len(config.flows)} flows')
"
```

### System Installation (If You Want Full Installation)
```bash
# Only run this if you want system-wide installation
sudo ./install.sh

# Then configure
sudo cp etc/pysyslog/main.ini.example /etc/pysyslog/main.ini
sudo systemctl restart pysyslog
```

## Troubleshooting

### "No such file or directory" for /etc/pysyslog
- **Cause**: You're in development mode, not system installation
- **Solution**: Use `etc/pysyslog/main.ini.example` instead of `/etc/pysyslog/main.ini`

### "Unit pysyslog.service not found"
- **Cause**: System installation hasn't been done
- **Solution**: Either run `sudo ./install.sh` OR continue using development mode

### Want to test without system installation?
- ✅ You're already set up correctly!
- ✅ Just use: `python3 -m pysyslog -c etc/pysyslog/main.ini.example`
- ✅ No sudo needed!

