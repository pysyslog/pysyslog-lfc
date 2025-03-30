# Numeric Filter

The numeric filter allows comparing numeric field values against specified values using various operators. It supports integer and floating-point comparisons with proper type conversion and validation.

## Configuration

```ini
filter.type = numeric
filter.field = severity
filter.op = between
filter.min = 3
filter.max = 5
```

### Required Parameters

- `filter.type`: Must be "numeric"
- `filter.field`: Field to compare (required)
- `filter.op`: Comparison operator (required)
- `filter.value`: Numeric value to compare against (required for single-value operations)

### Optional Parameters

- `filter.min`: Lower bound for range operations
- `filter.max`: Upper bound for range operations
- `filter.stage`: Where to apply the filter (default: parser)
- `filter.invert`: Whether to invert the match (default: false)

### Operators

1. Single Value Operations:
   - `eq`: Equal to
   - `ne`: Not equal to
   - `gt`: Greater than
   - `ge`: Greater than or equal
   - `lt`: Less than
   - `le`: Less than or equal

2. Range Operations:
   - `between`: Value is between min and max (inclusive)
   - `outside`: Value is outside min and max (exclusive)

## Examples

### Basic Comparison
```ini
filter.type = numeric
filter.field = severity
filter.op = ge
filter.value = 3
```

### Range Check
```ini
filter.type = numeric
filter.field = response_time
filter.op = between
filter.min = 100
filter.max = 1000
```

### Inverted Match
```ini
filter.type = numeric
filter.field = status_code
filter.op = between
filter.min = 400
filter.max = 599
filter.invert = true
```

## Field Value Handling

1. Type Conversion:
   - Integer values are converted to float
   - String values are parsed as float
   - Invalid values are treated as false

2. Null Handling:
   - Missing fields return false
   - Null values return false
   - Invalid types return false

## Security Limits

- Maximum value: 1e308
- Minimum value: -1e308
- Maximum precision: 15 decimal places

## Performance Considerations

1. Operation Cost:
   - Single value operations: O(1)
   - Range operations: O(1)
   - Type conversion: O(1)

2. Memory Usage:
   - Constant memory per filter
   - No additional storage needed

## Error Handling

1. Configuration Errors:
   - Invalid operator
   - Missing required parameters
   - Invalid numeric values

2. Runtime Errors:
   - Type conversion failures
   - Field access errors
   - Value range errors

## Example Use Cases

### Error Level Filtering
```ini
[flow.errors]
name.type = flow
name.description = "Error Logs"
input.type = file
input.path = /var/log/application.log
parser.type = rfc3164

# Filter errors and warnings
filter.type = numeric
filter.field = severity
filter.op = ge
filter.value = 3

output.type = file
output.path = /var/log/errors.log
```

### Response Time Monitoring
```ini
[flow.slow]
name.type = flow
name.description = "Slow Requests"
input.type = file
input.path = /var/log/access.log
parser.type = regex
parser.pattern = (?P<response_time>\d+)

# Filter slow requests
filter.type = numeric
filter.field = response_time
filter.op = gt
filter.value = 1000

output.type = file
output.path = /var/log/slow.log
```

### Status Code Range
```ini
[flow.status]
name.type = flow
name.description = "Status Codes"
input.type = file
input.path = /var/log/access.log
parser.type = regex
parser.pattern = (?P<status>\d{3})

# Filter error status codes
filter.type = numeric
filter.field = status
filter.op = between
filter.min = 400
filter.max = 599

output.type = file
output.path = /var/log/errors.log
``` 