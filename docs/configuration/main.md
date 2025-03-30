# Main Configuration

The main configuration file is located at:
- Linux/macOS: `/etc/pysyslog/main.ini`
- Windows: `C:\ProgramData\pysyslog\main.ini`

## Settings Section

```ini
[settings]
log_level = info
time_input_format = auto
buffering = enabled
buffer_type = memory
flush_every = 1s
max_buffer = 10000
on_overflow = block
metrics = enabled
```

### Available Settings

- `log_level`: Set the logging level (debug, info, warning, error)
- `time_input_format`: Time format for input parsing (auto, rfc3164, iso8601)
- `buffering`: Enable/disable buffering
- `buffer_type`: Type of buffer (memory, disk)
- `flush_every`: How often to flush the buffer
- `max_buffer`: Maximum number of messages in buffer
- `on_overflow`: What to do when buffer is full (block, drop)
- `metrics`: Enable/disable metrics collection

## Components Section

```ini
[use]
components = input.unixsock, input.flow, input.file, parser.rfc3164, parser.passthrough, parser.regex, output.memory, output.file, output.tcp

include = /etc/pysyslog/conf.d/*.ini
```

### Available Components

#### Input Components
- `input.unixsock`: Unix domain socket input
- `input.flow`: Flow chaining input
- `input.file`: File input with tailing support

#### Parser Components
- `parser.rfc3164`: RFC 3164 syslog parser
- `parser.passthrough`: Pass-through parser
- `parser.regex`: Regular expression parser

#### Output Components
- `output.memory`: In-memory output for flow chaining
- `output.file`: File output with rotation
- `output.tcp`: TCP output with reconnection

### Include Directive

The `include` directive specifies where to look for flow configuration files. By default, it looks in `/etc/pysyslog/conf.d/*.ini`. 