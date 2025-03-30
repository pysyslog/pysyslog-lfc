# Filter Components

Filter components are used to filter log messages based on various conditions. PySyslog supports three types of filter components:

## Regex Filter

Filters messages using regular expressions.

```ini
[flow.regex_filter]
filter.type = regex
filter.pattern = ERROR|WARNING
filter.field = message
filter.invert = false
filter.case_sensitive = true
```

### Configuration Options

- `filter.type`: Must be `regex`
- `filter.pattern`: Regular expression
  - Required
  - Supports capture groups
- `filter.field`: Field to match
  - Default: `message`
  - Options: Any parsed field
- `filter.invert`: Invert match
  - Default: `false`
  - Options: `true`, `false`
- `filter.case_sensitive`: Case sensitivity
  - Default: `true`
  - Options: `true`, `false`

### Pattern Examples

1. Error Messages:
```ini
filter.pattern = (ERROR|WARNING|CRITICAL)
```

2. IP Addresses:
```ini
filter.pattern = \b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b
```

3. Email Addresses:
```ini
filter.pattern = [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
```

## Level Filter

Filters messages based on log levels.

```ini
[flow.level_filter]
filter.type = level
filter.levels = ERROR,WARNING
filter.invert = false
filter.field = level
```

### Configuration Options

- `filter.type`: Must be `level`
- `filter.levels`: Log levels
  - Required
  - Comma-separated list
- `filter.invert`: Invert match
  - Default: `false`
  - Options: `true`, `false`
- `filter.field`: Field to match
  - Default: `level`
  - Options: Any parsed field

### Supported Levels

1. Standard Levels:
   - `DEBUG`
   - `INFO`
   - `WARNING`
   - `ERROR`
   - `CRITICAL`

2. Syslog Levels:
   - `EMERG`
   - `ALERT`
   - `CRIT`
   - `ERR`
   - `WARNING`
   - `NOTICE`
   - `INFO`
   - `DEBUG`

## Field Filter

Filters messages based on field values.

```ini
[flow.field_filter]
filter.type = field
filter.field = status
filter.operator = eq
filter.value = 404
filter.invert = false
```

### Configuration Options

- `filter.type`: Must be `field`
- `filter.field`: Field to match
  - Required
  - Any parsed field
- `filter.operator`: Comparison operator
  - Required
  - See operators below
- `filter.value`: Value to match
  - Required
  - Type depends on field
- `filter.invert`: Invert match
  - Default: `false`
  - Options: `true`, `false`

### Operators

1. Numeric:
   - `eq`: Equal to
   - `ne`: Not equal to
   - `gt`: Greater than
   - `ge`: Greater than or equal
   - `lt`: Less than
   - `le`: Less than or equal

2. String:
   - `eq`: Equal to
   - `ne`: Not equal to
   - `contains`: Contains substring
   - `startswith`: Starts with
   - `endswith`: Ends with
   - `matches`: Matches regex

3. Boolean:
   - `eq`: Equal to
   - `ne`: Not equal to

## Common Settings

All filter components support these common settings:

```ini
[flow.common]
filter.enabled = true
filter.batch_size = 100
filter.max_matches = 1000
filter.timeout = 5s
```

### Common Options

- `filter.enabled`: Enable/disable filter
  - Default: `true`
  - Options: `true`, `false`
- `filter.batch_size`: Messages per batch
  - Default: `100`
  - Range: `1` to `1000`
- `filter.max_matches`: Maximum matches
  - Default: `1000`
  - Range: `100` to `10000`
- `filter.timeout`: Filter timeout
  - Default: `5s`
  - Format: `<number><unit>` (e.g., `5s`, `1m`)

## Error Handling

Filter components handle errors gracefully:

1. Pattern errors:
   - Invalid regex
   - Missing fields
   - Type mismatches

2. Field errors:
   - Missing fields
   - Invalid operators
   - Value conversion

3. Performance errors:
   - Timeout handling
   - Resource limits
   - Memory protection

## Performance Considerations

1. Pattern optimization:
   - Compiled regex
   - Efficient matching
   - Memory usage

2. Field access:
   - Field caching
   - Type conversion
   - Value comparison

3. Batch processing:
   - Larger batches for throughput
   - Smaller batches for latency
   - Configure based on needs

## Example Configurations

### Error Logging

```ini
[flow.errors]
name.type = flow
name.description = "Error Logs"
input.type = file
input.path = /var/log/application.log
parser.type = rfc3164
filter.type = regex
filter.pattern = (ERROR|WARNING|CRITICAL)
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
filter.type = field
filter.field = status
filter.operator = ge
filter.value = 400
output.type = file
output.path = /var/log/errors.log
```

### Level-Based Filtering

```ini
[flow.levels]
name.type = flow
name.description = "Log Levels"
input.type = file
input.path = /var/log/application.log
parser.type = rfc3164
filter.type = level
filter.levels = ERROR,CRITICAL
output.type = tcp
output.host = logserver.example.com
output.port = 514
``` 