# Flow Components

Flow components define the processing pipeline for log messages. Each flow consists of an input component, optional parser components, and an output component.

## Basic Flow

A simple flow that reads from a file and writes to another file.

```ini
[flow.basic]
name.type = flow
name.description = "Basic Log Processing"
input.type = file
input.path = /var/log/application.log
parser.type = rfc3164
output.type = file
output.path = /var/log/processed.log
```

### Configuration Options

- `name.type`: Must be `flow`
- `name.description`: Flow description
  - Required
  - Human-readable text
- `input.type`: Input component type
  - Required
  - See input components
- `parser.type`: Parser component type
  - Optional
  - See parser components
- `output.type`: Output component type
  - Required
  - See output components

## Chained Flow

A flow that receives input from another flow.

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

### Flow Chaining

1. Source Flow:
   - Reads from file
   - Parses RFC 3164
   - Outputs to memory

2. Processor Flow:
   - Reads from memory
   - Parses with regex
   - Outputs to file

## Filtered Flow

A flow that filters messages based on conditions.

```ini
[flow.filtered]
name.type = flow
name.description = "Filtered Logs"
input.type = file
input.path = /var/log/application.log
parser.type = rfc3164
filter.type = regex
filter.pattern = ERROR|WARNING
output.type = file
output.path = /var/log/errors.log
```

### Filter Options

- `filter.type`: Filter type
  - Options: `regex`, `level`, `field`
- `filter.pattern`: Filter pattern
  - For regex: Regular expression
  - For level: Log levels
  - For field: Field conditions

## Parallel Flow

A flow that processes messages in parallel.

```ini
[flow.parallel]
name.type = flow
name.description = "Parallel Processing"
input.type = file
input.path = /var/log/application.log
parser.type = rfc3164
parallel.workers = 4
parallel.batch_size = 100
output.type = file
output.path = /var/log/processed.log
```

### Parallel Options

- `parallel.workers`: Number of workers
  - Default: `4`
  - Range: `1` to `16`
- `parallel.batch_size`: Batch size
  - Default: `100`
  - Range: `10` to `1000`

## Common Settings

All flows support these common settings:

```ini
[flow.common]
name.type = flow
name.description = "Common Flow"
enabled = true
batch_size = 100
max_retries = 3
retry_interval = 5s
```

### Common Options

- `enabled`: Enable/disable flow
  - Default: `true`
  - Options: `true`, `false`
- `batch_size`: Messages per batch
  - Default: `100`
  - Range: `1` to `1000`
- `max_retries`: Maximum retries
  - Default: `3`
  - Range: `0` to `10`
- `retry_interval`: Retry delay
  - Default: `5s`
  - Format: `<number><unit>` (e.g., `5s`, `1m`)

## Error Handling

Flows handle errors gracefully:

1. Component errors:
   - Retry with backoff
   - Skip failed messages
   - Log error details

2. Flow errors:
   - Flow isolation
   - Resource cleanup
   - State recovery

3. Chain errors:
   - Buffer protection
   - Flow synchronization
   - Error propagation

## Performance Considerations

1. Flow design:
   - Component selection
   - Batch sizes
   - Parallel processing

2. Resource usage:
   - Memory limits
   - CPU utilization
   - I/O operations

3. Error handling:
   - Retry strategies
   - Error recovery
   - Resource cleanup

## Example Configurations

### System Logs

```ini
[flow.system]
name.type = flow
name.description = "System Logs"
input.type = unixsock
input.path = auto
parser.type = rfc3164
output.type = file
output.path = /var/log/pysyslog/system.log
output.rotation = enabled
output.max_size = 100M
output.max_files = 10
```

### Application Logs

```ini
[flow.application]
name.type = flow
name.description = "Application Logs"
input.type = file
input.path = /var/log/application.log
parser.type = regex
parser.pattern = (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(?P<level>\w+)\] (?P<message>.*)
output.type = tcp
output.host = logserver.example.com
output.port = 514
output.ssl = enabled
```

### Custom Processing

```ini
[flow.custom]
name.type = flow
name.description = "Custom Processing"
input.type = file
input.path = /var/log/custom.log
parser.type = passthrough
filter.type = regex
filter.pattern = ERROR|WARNING
parallel.workers = 4
output.type = file
output.path = /var/log/errors.log
output.format = json
```
