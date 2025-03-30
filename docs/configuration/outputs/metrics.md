# Metrics Output Component

The metrics output component exports log-based metrics in various formats. It supports multiple metric types and can export to Prometheus or custom HTTP endpoints.

## Dependencies
- `aiohttp`: For HTTP server and client functionality

## Configuration
```yaml
output:
  type: metrics
  format: "prometheus"    # Export format
  interval: 15           # Export interval (seconds)
  metrics:
    - name: "error_count"
      type: "counter"     # counter, gauge, or histogram
      pattern: "ERROR"
      labels: ["source"]
      value: 1
      buckets: [1, 5, 10, 50, 100]  # For histograms
  
  # Prometheus configuration
  prometheus:
    port: 9090
    path: "/metrics"
  
  # Custom format configuration
  custom:
    url: "https://api.example.com/metrics"
    method: "POST"
    headers:
      Content-Type: "application/json"
    template: "{metrics}"
```

## Metric Types

### Counter
- Monotonically increasing value
- Resets on restart
- Good for error counts, request counts
- Example: `error_count{source="app"} 42`

### Gauge
- Current value that can go up and down
- Latest value is preserved
- Good for memory usage, active connections
- Example: `active_users{service="web"} 123`

### Histogram
- Distribution of values
- Configurable buckets
- Good for response times, request sizes
- Example:
  ```
  response_time_bucket{le="0.1"} 100
  response_time_bucket{le="0.5"} 200
  response_time_bucket{le="1.0"} 300
  response_time_sum 150.5
  response_time_count 300
  ```

## Export Formats

### Prometheus Format
- Standard Prometheus text format
- Exposed via HTTP endpoint
- Compatible with Prometheus server
- Example:
  ```
  # HELP error_count Total number of errors
  # TYPE error_count counter
  error_count{source="app"} 42
  error_count{source="db"} 15
  ```

### Custom Format
- Template-based formatting
- HTTP POST to specified endpoint
- Flexible JSON/XML output
- Example:
  ```json
  {
    "metrics": {
      "error_count": {
        "app": 42,
        "db": 15
      },
      "active_users": {
        "web": 123
      }
    }
  }
  ```

## Features
- Label support for metrics
- Pattern-based matching
- Batch updates
- Custom templates
- Multiple metric types
- Automatic metric naming
- Bucket configuration for histograms

## Example Configurations

### Error Rate Monitoring
```yaml
output:
  type: metrics
  format: "prometheus"
  metrics:
    - name: "error_count"
      type: "counter"
      pattern: "ERROR"
      labels: ["source", "level"]
      value: 1
    - name: "error_rate"
      type: "gauge"
      pattern: "ERROR"
      labels: ["source"]
      value: 1
```

### Response Time Monitoring
```yaml
output:
  type: metrics
  format: "prometheus"
  metrics:
    - name: "response_time"
      type: "histogram"
      pattern: "Response time: (\d+)ms"
      labels: ["endpoint"]
      value: "$1"
      buckets: [10, 50, 100, 200, 500, 1000]
```

### Custom JSON Output
```yaml
output:
  type: metrics
  format: "custom"
  metrics:
    - name: "error_count"
      type: "counter"
      pattern: "ERROR"
      labels: ["source"]
      value: 1
  custom:
    url: "https://api.example.com/metrics"
    template: |
      {
        "timestamp": "{timestamp}",
        "metrics": {
          "errors": {metrics.counters.error_count},
          "sources": {metrics.counters.error_count.labels}
        }
      }
```

## Installation
```bash
pip install aiohttp
``` 