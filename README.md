
[![Pylint](https://github.com/pysyslog/pysyslog-lfc/actions/workflows/pylint.yml/badge.svg)](https://github.com/pysyslog/pysyslog-lfc/actions/workflows/pylint.yml)
![Python Versions](https://img.shields.io/badge/python-3.8%20|%203.9%20|%203.10-blue)
[![License](https://img.shields.io/github/license/pysyslog/pysyslog-lfc.svg)](https://github.com/pysyslog/pysyslog-lfc/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/pysyslog/pysyslog-lfc.svg)](https://github.com/pysyslog/pysyslog-lfc/commits/main)


# PySyslog LFC

A lightweight, modular log processor with flow-based configuration.

## Features

- Flow-based log processing model
- Dynamic component loading
- Support for various input sources (Unix socket, file, flow chaining)
- Multiple parser types (RFC 3164, regex, passthrough)
- Flexible output options (file, TCP, memory for flow chaining)
- JSON-formatted logs
- Systemd service integration
- Clean, modern design without legacy syslog terminology

## Installation

### Manual Installation

#### Prerequisites

- Python 3.8 or higher
- pip3
- git

#### Linux/macOS

1. Clone the repository:
```bash
git clone https://github.com/rsyslog/pysyslog-lfc.git
cd pysyslog-lfc
```

2. Run the installation script:
```bash
sudo ./install.sh
```

#### Windows

1. Clone the repository:
```cmd
git clone https://github.com/rsyslog/pysyslog-lfc.git
cd pysyslog-lfc
```

2. Run the installation script as administrator:
```cmd
install.bat
```

### Development Installation

1. Clone the repository:
```bash
git clone https://github.com/rsyslog/pysyslog-lfc.git
cd pysyslog-lfc
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install in development mode:
```bash
pip install -e .
```

## Configuration

For detailed configuration documentation, see:
- [Main Configuration](docs/configuration/main.md)
- [Flow Configuration](docs/configuration/flows.md)

## Usage

### Command Line

Start PySyslog LFC:
```bash
# Linux/macOS
sudo pysyslog

# Windows
pysyslog
```

### Service Management

#### Linux (systemd)
```bash
sudo systemctl start pysyslog
sudo systemctl stop pysyslog
sudo systemctl restart pysyslog
sudo systemctl status pysyslog
```

#### macOS (launchd)
```bash
sudo launchctl start com.pysyslog
sudo launchctl stop com.pysyslog
sudo launchctl unload /Library/LaunchDaemons/com.pysyslog.plist
sudo launchctl load /Library/LaunchDaemons/com.pysyslog.plist
```

#### Windows
```cmd
net start pysyslog
net stop pysyslog
```

### Viewing Logs

#### Linux
```bash
sudo journalctl -u pysyslog -f
```

#### macOS
```bash
sudo log show --predicate 'process == "pysyslog"' --last 5m
```

#### Windows
```cmd
Get-EventLog -LogName Application -Source pysyslog
```

## Development

### Project Structure

```
pysyslog-lfc/
├── bin/                    # Executable scripts
├── docs/                   # Documentation
│   └── configuration/      # Configuration docs
├── etc/                    # Configuration files
│   ├── pysyslog/
│   │   ├── main.ini
│   │   └── conf.d/
│   ├── systemd/           # Linux service files
│   ├── launchd/           # macOS service files
│   └── windows/           # Windows service files
├── lib/                    # Python package
│   └── pysyslog/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── flow.py
│       ├── components.py
│       ├── inputs/         # Input components
|       ├── filters/        # Filter components
│       ├── parsers/        # Parser components
│       └── outputs/        # Output components
├── install.sh             # Linux/macOS installation script
├── install.bat            # Windows installation script
├── requirements.txt       # Python dependencies
└── setup.py              # Python package setup
```

### Adding New Components

1. Create a new component file in the appropriate directory:
   - `inputs/` for input components
   - `filters/` for filter components
   - `parsers/` for parser components
   - `outputs/` for output components
2. Implement the required interface
3. Add the component to the `components` list in `main.ini`

## License

MIT License - see LICENSE file for details. 
