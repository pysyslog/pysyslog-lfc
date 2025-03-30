# Filter Components

Filter components are used to filter log messages based on various conditions. Filters must be used as part of a flow and cannot exist independently.

## Overview

Filters in PySyslog LFC are designed to be:
1. Part of a flow - filters cannot exist independently
2. Stage-specific - can be applied at input, parser, or output stages
3. Type-safe - with proper validation and error handling
4. Resource-efficient - with security limits and performance considerations

## Basic Usage

Filters are configured within a flow's configuration:

```ini
[flow.filtered]
name.type = flow
name.description = "Filtered Logs"
input.type = file
input.path = /var/log/application.log
parser.type = rfc3164

# Filter configuration
filter.type = numeric
filter.field = severity
filter.op = between
filter.min = 3
filter.max = 5
filter.stage = parser

output.type = file
output.path = /var/log/errors.log
```

### Filter Configuration

Each filter in a flow must have:
- `filter.type`: Filter type (required)
- `filter.field`: Field to evaluate (required)
- `filter.op`: Operation to apply (required)
- `filter.value`: Value to compare (required)
- `filter.stage`: Where to apply the filter (optional, default: parser)

Additional parameters depend on the filter type:
- `filter.min`: Lower bound for range operations
- `filter.max`: Upper bound for range operations
- `filter.pattern`: Regex pattern for regex operations

The flow name is automatically added to the filter configuration.

## Filter Types

### Basic Filters
- [Numeric Filter](filters/numeric.md) - Compare numeric values
- [Text Filter](filters/text.md) - Compare text values
- [Regex Filter](filters/regex.md) - Match against regex patterns
- [Field Filter](filters/field.md) - Check field existence and values

### Data Type Filters
- [Boolean Filter](filters/boolean.md) - Boolean operations
- [List Filter](filters/list.md) - List operations
- [Timestamp Filter](filters/timestamp.md) - Date/time operations
- [Level Filter](filters/level.md) - Log level operations

### Network Filters
- [IP Filter](filters/ip.md) - IP address operations
- [Port Filter](filters/port.md) - Port number operations
- [Protocol Filter](filters/protocol.md) - Protocol operations
- [Hostname Filter](filters/hostname.md) - Hostname operations

### Format Filters
- [URL Filter](filters/url.md) - URL operations
- [Email Filter](filters/email.md) - Email operations
- [JSON Filter](filters/json.md) - JSON operations
- [MIME Filter](filters/mime.md) - MIME type operations

### Special Filters
- [Hash Filter](filters/hash.md) - Hash operations
- [UUID Filter](filters/uuid.md) - UUID operations
- [Version Filter](filters/version.md) - Version number operations
- [Path Filter](filters/path.md) - File path operations

## Filter Stages

Filters can be applied at different stages of the flow:

1. Input Stage:
   ```ini
   filter.stage = input
   ```
   - Applied to raw input data
   - Field is always "raw"
   - Useful for pre-parsing filtering

2. Parser Stage (default):
   ```ini
   filter.stage = parser
   ```
   - Applied to parsed message data
   - Can access any parsed field
   - Most common stage

3. Output Stage:
   ```ini
   filter.stage = output
   ```
   - Applied to final message data
   - Can access all fields
   - Useful for final filtering

## Security Limits

Filters enforce security limits:
- Maximum pattern length: 1000 characters
- Maximum list size: 1000 items
- Maximum field length: 1000 characters
- Maximum string length: 10000 characters

## Error Handling

1. Configuration Errors:
   - Invalid filter type
   - Missing required parameters
   - Invalid parameter values

2. Runtime Errors:
   - Invalid message format
   - Missing fields
   - Type conversion errors

3. Resource Errors:
   - Memory limits
   - CPU limits
   - I/O limits

## Performance Considerations

1. Filter Stage:
   - Input stage: Pre-parsing filtering
   - Parser stage: Post-parsing filtering
   - Output stage: Final filtering

2. Operation Cost:
   - Simple operations (eq, ne)
   - String operations (contains, matches)
   - Range operations (between)

3. Resource Usage:
   - Memory per filter
   - CPU per filter
   - I/O operations

## Example Configurations

### Error Logging
```ini
[flow.errors]
name.type = flow
name.description = "Error Logs"
input.type = file
input.path = /var/log/application.log
parser.type = rfc3164

# Level filter
filter.type = numeric
filter.field = severity
filter.op = ge
filter.value = 3

output.type = file
output.path = /var/log/errors.log
```

### Status Code Filtering
```ini
[flow.status]
name.type = flow
name.description = "Status Codes"
input.type = file
input.path = /var/log/access.log
parser.type = regex
parser.pattern = (?P<status>\d{3})

# Status code filter
filter.type = numeric
filter.field = status
filter.op = between
filter.min = 400
filter.max = 599

output.type = file
output.path = /var/log/errors.log
```

### Complex Filtering
```ini
[flow.complex]
name.type = flow
name.description = "Complex Filtering"
input.type = file
input.path = /var/log/application.log
parser.type = rfc3164

# Message filter
filter.type = regex
filter.field = message
filter.op = match
filter.pattern = ^ERROR.*
filter.stage = parser

output.type = tcp
output.host = logserver.example.com
output.port = 514
``` 