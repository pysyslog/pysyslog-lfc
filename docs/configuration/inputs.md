# Input Components

Input components are responsible for receiving log messages from various sources. PySyslog supports three types of input components:

## Unix Socket Input

Receives logs from a Unix domain socket, typically used for local system logs.

```ini
[flow.unix]
input.type = unixsock
input.path = auto
input.buffer_size = 65536
input.timeout = 1s
```

### Configuration Options

- `input.type`: Must be `unixsock`
- `input.path`: Path to Unix socket
  - `auto`: Auto-detect based on distribution
  - Custom path: `/path/to/socket`
- `input.buffer_size`: Socket buffer size
  - Default: `65536` bytes
  - Range: `1024` to `1048576` bytes
- `input.timeout`: Socket timeout
  - Default: `1s`
  - Format: `<number><unit>` (e.g., `5s`, `1m`)

### Distribution-Specific Socket Paths

- Ubuntu/Debian: `/run/systemd/journal/syslog`
- RHEL/CentOS: `/run/systemd/journal/syslog`
- SUSE: `/run/systemd/journal/syslog`
- Alpine: `/dev/log`
- macOS: `/var/run/syslog`

## File Input

Reads logs from files with support for file rotation and tailing.

```ini
[flow.file]
input.type = file
input.path = /var/log/application.log
input.poll_interval = 1s
input.start_position = end
input.encoding = utf-8
input.follow = true
input.rotation_check = true
```

### Configuration Options

- `input.type`: Must be `file`
- `input.path`: Path to log file
  - Required
  - Supports glob patterns
- `input.poll_interval`: How often to check for changes
  - Default: `1s`
  - Format: `<number><unit>` (e.g., `5s`, `1m`)
- `input.start_position`: Where to start reading
  - Default: `end`
  - Options: `start`, `end`
- `input.encoding`: File encoding
  - Default: `utf-8`
  - Common options: `ascii`, `latin1`, `utf-16`
- `input.follow`: Whether to follow file changes
  - Default: `true`
  - Options: `true`, `false`
- `input.rotation_check`: Check for file rotation
  - Default: `true`
  - Options: `true`, `false`

### File Rotation Detection

The file input component can detect file rotation by:
1. Monitoring file size changes
2. Checking file modification time
3. Verifying file inode changes

## Flow Input

Receives logs from other flows, enabling log processing pipelines.

```ini
[flow.chain]
input.type = flow
input.source = flow.source
input.buffer_size = 1000
input.timeout = 5s
```

### Configuration Options

- `input.type`: Must be `flow`
- `input.source`: Name of source flow
  - Required
  - Must reference existing flow
- `input.buffer_size`: Queue size
  - Default: `1000`
  - Range: `100` to `10000`
- `input.timeout`: Wait time for messages
  - Default: `5s`
  - Format: `<number><unit>` (e.g., `5s`, `1m`)

### Flow Chaining Example

```ini
[flow.source]
name.type = flow
name.description = "Source Logs"
input.type = file
input.path = /var/log/source.log
parser.type = rfc3164
output.type = memory

[flow.processor]
name.type = flow
name.description = "Processed Logs"
input.type = flow
input.source = flow.source
parser.type = regex
parser.pattern = (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (?P<level>\w+) (?P<message>.*)
output.type = file
output.path = /var/log/processed.log
```

## Common Settings

All input components support these common settings:

```ini
[flow.common]
input.enabled = true
input.batch_size = 100
input.max_message_size = 65536
input.retry_interval = 5s
input.max_retries = 3
```

### Common Options

- `input.enabled`: Enable/disable input
  - Default: `true`
  - Options: `true`, `false`
- `input.batch_size`: Messages per batch
  - Default: `100`
  - Range: `1` to `1000`
- `input.max_message_size`: Maximum message size
  - Default: `65536` bytes
  - Range: `1024` to `1048576` bytes
- `input.retry_interval`: Time between retries
  - Default: `5s`
  - Format: `<number><unit>` (e.g., `5s`, `1m`)
- `input.max_retries`: Maximum retry attempts
  - Default: `3`
  - Range: `0` to `10`

## Error Handling

Input components handle errors gracefully:

1. Connection errors:
   - Retry with exponential backoff
   - Log error details
   - Continue when possible

2. File errors:
   - Handle file rotation
   - Reopen on truncation
   - Skip corrupted data

3. Flow errors:
   - Buffer overflow protection
   - Timeout handling
   - Source flow validation

## Performance Considerations

1. Buffer sizes:
   - Larger buffers for high throughput
   - Smaller buffers for low latency
   - Adjust based on message size

2. Polling intervals:
   - Shorter for real-time needs
   - Longer for resource efficiency
   - Balance based on requirements

3. Batch processing:
   - Larger batches for throughput
   - Smaller batches for latency
   - Configure based on use case
