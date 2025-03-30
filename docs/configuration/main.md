# Main Configuration

The main configuration file is located at:
- Linux/macOS: `/etc/pysyslog/main.ini`
- Windows: `C:\ProgramData\pysyslog\main.ini`

## Settings Section

```ini
[settings]
# Logging level (debug, info, warning, error)
log_level = info

# Time format for input parsing (auto, rfc3164, iso8601)
time_input_format = auto

# Buffer settings
buffering = enabled
buffer_type = memory
flush_every = 1s
max_buffer = 10000
on_overflow = block

# Enable/disable metrics collection
metrics = enabled
```

### Available Settings

#### Logging
- `log_level`: Set the logging level
  - Default: `info`
  - Options: `debug`, `info`, `warning`, `error`
  - Description: Controls the verbosity of log output

#### Time Format
- `time_input_format`: Time format for input parsing
  - Default: `auto`
  - Options: `auto`, `rfc3164`, `iso8601`
  - Description: Specifies how to parse timestamps in input messages

#### Buffering
- `buffering`: Enable/disable buffering
  - Default: `enabled`
  - Options: `enabled`, `disabled`
  - Description: Controls whether messages are buffered before processing

- `buffer_type`: Type of buffer
  - Default: `memory`
  - Options: `memory`, `disk`
  - Description: Specifies where to store buffered messages

- `flush_every`: How often to flush the buffer
  - Default: `1s`
  - Format: `<number><unit>` (e.g., `5s`, `1m`)
  - Description: Controls buffer flush frequency

- `max_buffer`: Maximum number of messages in buffer
  - Default: `10000`
  - Description: Maximum number of messages to keep in buffer

- `on_overflow`: What to do when buffer is full
  - Default: `block`
  - Options: `block`, `drop`
  - Description: Controls behavior when buffer reaches max_buffer

#### Metrics
- `metrics`: Enable/disable metrics collection
  - Default: `enabled`
  - Options: `enabled`, `disabled`
  - Description: Controls collection of performance metrics

## Components Section

```ini
[use]
# List of available components
components = input.unixsock, input.flow, input.file, parser.rfc3164, parser.passthrough, parser.regex, output.memory, output.file, output.tcp

# Include additional configuration files
include = /etc/pysyslog/conf.d/*.ini
```

### Available Components

#### Input Components
- `input.unixsock`: Unix domain socket input
  - Receives logs from local Unix socket
  - Auto-detects socket path based on distribution

- `input.flow`: Flow chaining input
  - Receives logs from other flows
  - Enables log processing pipelines

- `input.file`: File input with tailing support
  - Reads logs from files
  - Supports file rotation detection
  - Configurable polling interval

#### Parser Components
- `parser.rfc3164`: RFC 3164 syslog parser
  - Parses standard syslog messages
  - Supports multiple formats
  - Validates message structure

- `parser.passthrough`: Pass-through parser
  - Passes messages without parsing
  - Supports format conversion

- `parser.regex`: Regular expression parser
  - Custom parsing using regex patterns
  - Flexible field extraction

#### Output Components
- `output.memory`: In-memory output for flow chaining
  - Stores messages in memory queue
  - Enables flow chaining

- `output.file`: File output with rotation
  - Writes logs to files
  - Supports log rotation
  - Configurable compression

- `output.tcp`: TCP output with reconnection
  - Sends logs over TCP
  - Supports SSL/TLS
  - Connection pooling

### Include Directive
The `include` directive specifies where to look for flow configuration files:
- Default: `/etc/pysyslog/conf.d/*.ini`
- Supports glob patterns
- Multiple patterns can be specified
- Files are loaded in alphabetical order

## Example Configuration

```ini
[settings]
log_level = info
time_input_format = auto
buffering = enabled
buffer_type = memory
flush_every = 5s
max_buffer = 5000
on_overflow = block
metrics = enabled

[use]
components = input.unixsock, input.file, parser.rfc3164, output.file, output.tcp
include = /etc/pysyslog/conf.d/*.ini

[flow.local]
name.type = flow
name.description = "Local System Logs"
input.type = unixsock
input.path = auto
parser.type = rfc3164
output.type = file
output.path = /var/log/pysyslog/system.log
output.rotation = enabled
output.max_size = 100M
output.max_files = 10
output.compress = true
``` 