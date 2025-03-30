# Output Components

Output components are responsible for sending processed log messages to various destinations. PySyslog supports three types of output components:

## File Output

Writes logs to files with support for rotation and compression.

```ini
[flow.file]
output.type = file
output.path = /var/log/pysyslog/output.log
output.rotation = enabled
output.max_size = 100M
output.max_files = 10
output.compress = true
output.format = json
output.flush_interval = 5s
```

### Configuration Options

- `output.type`: Must be `file`
- `output.path`: Path to output file
  - Required
  - Supports directory creation
- `output.rotation`: Enable/disable rotation
  - Default: `enabled`
  - Options: `enabled`, `disabled`
- `output.max_size`: Maximum file size
  - Default: `100M`
  - Format: `<number><unit>` (e.g., `1G`, `500M`)
- `output.max_files`: Maximum rotated files
  - Default: `10`
  - Range: `1` to `100`
- `output.compress`: Compress rotated files
  - Default: `true`
  - Options: `true`, `false`
- `output.format`: Output format
  - Default: `json`
  - Options: `json`, `text`, `syslog`
- `output.flush_interval`: Flush frequency
  - Default: `5s`
  - Format: `<number><unit>` (e.g., `5s`, `1m`)

### File Rotation

Rotated files follow this pattern:
- `output.log`
- `output.log.1`
- `output.log.2.gz`
- `output.log.3.gz`
- etc.

## TCP Output

Sends logs over TCP with SSL/TLS support and connection pooling.

```ini
[flow.tcp]
output.type = tcp
output.host = logserver.example.com
output.port = 514
output.ssl = enabled
output.cert_file = /path/to/cert.pem
output.key_file = /path/to/key.pem
output.ca_file = /path/to/ca.pem
output.pool_size = 5
output.timeout = 30s
output.retry_interval = 5s
output.max_retries = 3
```

### Configuration Options

- `output.type`: Must be `tcp`
- `output.host`: Server hostname/IP
  - Required
  - Supports DNS resolution
- `output.port`: Server port
  - Default: `514`
  - Range: `1` to `65535`
- `output.ssl`: Enable SSL/TLS
  - Default: `disabled`
  - Options: `enabled`, `disabled`
- `output.cert_file`: Client certificate
  - Required if SSL enabled
  - Path to PEM file
- `output.key_file`: Private key
  - Required if SSL enabled
  - Path to PEM file
- `output.ca_file`: CA certificate
  - Optional
  - Path to PEM file
- `output.pool_size`: Connection pool size
  - Default: `5`
  - Range: `1` to `50`
- `output.timeout`: Connection timeout
  - Default: `30s`
  - Format: `<number><unit>` (e.g., `5s`, `1m`)
- `output.retry_interval`: Retry delay
  - Default: `5s`
  - Format: `<number><unit>` (e.g., `5s`, `1m`)
- `output.max_retries`: Maximum retries
  - Default: `3`
  - Range: `0` to `10`

### SSL/TLS Configuration

When SSL is enabled:
1. Certificate validation
2. Mutual authentication
3. Cipher selection
4. Protocol version

## Memory Output

Stores logs in memory for flow chaining.

```ini
[flow.memory]
output.type = memory
output.queue_size = 1000
output.timeout = 5s
output.max_size = 100M
```

### Configuration Options

- `output.type`: Must be `memory`
- `output.queue_size`: Queue capacity
  - Default: `1000`
  - Range: `100` to `10000`
- `output.timeout`: Wait time for readers
  - Default: `5s`
  - Format: `<number><unit>` (e.g., `5s`, `1m`)
- `output.max_size`: Maximum memory usage
  - Default: `100M`
  - Format: `<number><unit>` (e.g., `1G`, `500M`)

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
output.type = file
output.path = /var/log/processed.log
```

## Common Settings

All output components support these common settings:

```ini
[flow.common]
output.enabled = true
output.batch_size = 100
output.format = json
output.compression = disabled
output.flush_interval = 5s
```

### Common Options

- `output.enabled`: Enable/disable output
  - Default: `true`
  - Options: `true`, `false`
- `output.batch_size`: Messages per batch
  - Default: `100`
  - Range: `1` to `1000`
- `output.format`: Output format
  - Default: `json`
  - Options: `json`, `text`, `syslog`
- `output.compression`: Enable compression
  - Default: `disabled`
  - Options: `enabled`, `disabled`
- `output.flush_interval`: Flush frequency
  - Default: `5s`
  - Format: `<number><unit>` (e.g., `5s`, `1m`)

## Error Handling

Output components handle errors gracefully:

1. Connection errors:
   - Retry with exponential backoff
   - Connection pooling
   - Failover support

2. File errors:
   - Safe file rotation
   - Disk space checks
   - Permission handling

3. Memory errors:
   - Queue overflow protection
   - Memory limit enforcement
   - Resource cleanup

## Performance Considerations

1. Batch processing:
   - Larger batches for throughput
   - Smaller batches for latency
   - Configure based on needs

2. Buffer management:
   - File buffering
   - Memory limits
   - Flush intervals

3. Connection pooling:
   - Pool size tuning
   - Idle connection cleanup
   - Connection reuse
