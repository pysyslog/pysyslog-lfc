# Parser Components

Parser components are responsible for parsing and validating log messages. PySyslog supports three types of parser components:

## RFC 3164 Parser

Parses standard syslog messages according to RFC 3164.

```ini
[flow.rfc3164]
parser.type = rfc3164
parser.validate = true
parser.timezone = auto
parser.max_message_size = 65536
parser.allow_invalid = false
```

### Configuration Options

- `parser.type`: Must be `rfc3164`
- `parser.validate`: Enable validation
  - Default: `true`
  - Options: `true`, `false`
- `parser.timezone`: Timezone handling
  - Default: `auto`
  - Options: `auto`, `utc`, `local`
- `parser.max_message_size`: Maximum size
  - Default: `65536` bytes
  - Range: `1024` to `1048576` bytes
- `parser.allow_invalid`: Allow invalid messages
  - Default: `false`
  - Options: `true`, `false`

### Message Format

RFC 3164 format:
```
<priority>timestamp hostname program[pid]: message
```

Example:
```
<34>Oct 11 22:14:15 mymachine su: 'su root' failed for lonvick on /dev/pts/8
```

### Validation Rules

1. Priority:
   - Range: 0-191
   - Facility: 0-23
   - Severity: 0-7

2. Timestamp:
   - Format: MMM DD HH:MM:SS
   - Month: Jan-Dec
   - Day: 1-31
   - Time: 24-hour format

3. Hostname:
   - Max length: 255 characters
   - Valid characters: letters, numbers, dots, hyphens

4. Program:
   - Max length: 32 characters
   - Optional PID in brackets

## Regex Parser

Parses logs using regular expressions.

```ini
[flow.regex]
parser.type = regex
parser.pattern = (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (?P<level>\w+) (?P<message>.*)
parser.validate = true
parser.timezone = auto
parser.max_message_size = 65536
parser.allow_invalid = false
```

### Configuration Options

- `parser.type`: Must be `regex`
- `parser.pattern`: Regular expression
  - Required
  - Named capture groups
- `parser.validate`: Enable validation
  - Default: `true`
  - Options: `true`, `false`
- `parser.timezone`: Timezone handling
  - Default: `auto`
  - Options: `auto`, `utc`, `local`
- `parser.max_message_size`: Maximum size
  - Default: `65536` bytes
  - Range: `1024` to `1048576` bytes
- `parser.allow_invalid`: Allow invalid messages
  - Default: `false`
  - Options: `true`, `false`

### Pattern Examples

1. Apache Log:
```ini
parser.pattern = (?P<ip>[\d.]+) - - \[(?P<timestamp>.*?)\] "(?P<request>.*?)" (?P<status>\d+) (?P<size>\d+)
```

2. Custom Application:
```ini
parser.pattern = (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(?P<level>\w+)\] (?P<component>\w+): (?P<message>.*)
```

## Pass-through Parser

Passes messages without parsing, with optional format conversion.

```ini
[flow.passthrough]
parser.type = passthrough
parser.format = json
parser.validate = false
parser.max_message_size = 65536
```

### Configuration Options

- `parser.type`: Must be `passthrough`
- `parser.format`: Output format
  - Default: `json`
  - Options: `json`, `text`, `syslog`
- `parser.validate`: Enable validation
  - Default: `false`
  - Options: `true`, `false`
- `parser.max_message_size`: Maximum size
  - Default: `65536` bytes
  - Range: `1024` to `1048576` bytes

### Format Conversion

1. JSON Input:
```json
{
  "timestamp": "2024-03-14T12:34:56",
  "level": "INFO",
  "message": "Application started"
}
```

2. Text Output:
```
2024-03-14T12:34:56 INFO Application started
```

## Common Settings

All parser components support these common settings:

```ini
[flow.common]
parser.enabled = true
parser.batch_size = 100
parser.timezone = auto
parser.max_message_size = 65536
parser.allow_invalid = false
```

### Common Options

- `parser.enabled`: Enable/disable parser
  - Default: `true`
  - Options: `true`, `false`
- `parser.batch_size`: Messages per batch
  - Default: `100`
  - Range: `1` to `1000`
- `parser.timezone`: Timezone handling
  - Default: `auto`
  - Options: `auto`, `utc`, `local`
- `parser.max_message_size`: Maximum size
  - Default: `65536` bytes
  - Range: `1024` to `1048576` bytes
- `parser.allow_invalid`: Allow invalid messages
  - Default: `false`
  - Options: `true`, `false`

## Error Handling

Parser components handle errors gracefully:

1. Validation errors:
   - Log error details
   - Skip invalid messages
   - Continue processing

2. Format errors:
   - Pattern matching
   - Field extraction
   - Type conversion

3. Size errors:
   - Message truncation
   - Buffer limits
   - Memory protection

## Performance Considerations

1. Pattern optimization:
   - Compiled regex
   - Efficient matching
   - Memory usage

2. Batch processing:
   - Larger batches for throughput
   - Smaller batches for latency
   - Configure based on needs

3. Validation overhead:
   - Selective validation
   - Field checking
   - Type conversion
