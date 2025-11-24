# Missing Components Documentation

This document lists components that are referenced in the configuration files but are not yet implemented in the codebase.

## Missing Input Components

### `input.unix`
- **Purpose**: Read logs from Unix domain sockets
- **Expected Options**:
  - `socket_path`: Path to the Unix socket (or "auto" for auto-detection)
- **Status**: Not implemented
- **Priority**: High (commonly used for syslog)

### `input.file`
- **Purpose**: Read logs from files (with tail/follow capability)
- **Expected Options**:
  - `path`: Path to the log file (or "auto" for auto-detection)
  - `log_type`: Type of log (e.g., "messages", "secure")
- **Status**: Not implemented
- **Priority**: High (essential for file-based log processing)

### `input.flow`
- **Purpose**: Chain flows together by reading from another flow's memory output
- **Expected Options**:
  - `name`: Name of the source flow
- **Status**: Not implemented
- **Priority**: Medium (enables flow chaining)

### `input.tcp`
- **Purpose**: Receive logs over TCP (syslog server)
- **Expected Options**:
  - `port`: TCP port to listen on
  - `bind`: IP address to bind to
- **Status**: Not implemented
- **Priority**: High (for remote syslog reception)

## Missing Parser Components

### `parser.rfc3164`
- **Purpose**: Parse RFC 3164 syslog messages
- **Expected Options**: None (standard format)
- **Status**: Not implemented
- **Priority**: High (standard syslog format)

### `parser.passthrough`
- **Purpose**: Pass through already-parsed messages without modification
- **Expected Options**: None
- **Status**: Not implemented
- **Priority**: Low (used for flow chaining)

### `parser.regex`
- **Purpose**: Parse log messages using regular expressions
- **Expected Options**:
  - `pattern`: Regular expression with named groups
- **Status**: Not implemented
- **Priority**: Medium (flexible parsing)

## Missing Output Components

### `output.file`
- **Purpose**: Write logs to files with rotation support
- **Expected Options**:
  - `path`: Path to the output file
  - `rotation`: Enable/disable log rotation
  - `max_size`: Maximum file size before rotation
  - `max_files`: Maximum number of rotated files to keep
- **Status**: Not implemented
- **Priority**: High (essential for file-based logging)

### `output.tcp`
- **Purpose**: Send logs over TCP to a remote server
- **Expected Options**:
  - `host`: Target hostname or IP
  - `port`: Target port
- **Status**: Not implemented
- **Priority**: Medium (for remote log forwarding)

## Implementation Notes

When implementing these components:

1. **Follow the base class pattern**: All components should inherit from the appropriate base class in `components/base.py`
2. **Register in registry**: Add entries to `BUILTIN_*` dictionaries in `components/registry.py`
3. **Use async/await**: All I/O operations should be asynchronous
4. **Handle errors gracefully**: Components should handle errors without crashing the flow
5. **Support context managers**: Components should work as async context managers
6. **Add tests**: Create tests in the `tests/` directory

## Current Working Components

The following components are fully implemented and working:

- **Inputs**: `memory`
- **Parsers**: `json`, `text`
- **Filters**: `field`
- **Outputs**: `stdout`, `memory`
- **Formats**: `json`, `text`

See `etc/pysyslog/main.ini.example` for a working configuration example using only implemented components.

