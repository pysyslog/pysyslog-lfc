# Alert Output Component

The alert output component sends notifications when log messages match specified patterns. It supports multiple notification channels including email, webhooks, and custom scripts.

## Dependencies
- `aiohttp`: For HTTP webhook functionality
- `smtplib`: For email functionality (built-in)

## Configuration
```yaml
output:
  type: alert
  channel: "email"        # Notification channel
  pattern: "ERROR"        # Pattern to match
  threshold: 5            # Matches before alert
  window: 60             # Time window (seconds)
  cooldown: 300          # Alert cooldown (seconds)
  
  # Email configuration
  email:
    smtp_host: "smtp.example.com"
    smtp_port: 587
    username: "user"
    password: "pass"
    from_addr: "alerts@example.com"
    to_addrs: ["admin@example.com"]
    subject: "Log Alert"
  
  # Webhook configuration
  webhook:
    url: "https://api.example.com/webhook"
    method: "POST"
    headers:
      Authorization: "Bearer token"
    template: "{message}"
  
  # Script configuration
  script:
    path: "/path/to/alert.sh"
    args: ["--level", "error"]
```

## Notification Channels

### Email Alerts
- Uses SMTP for sending emails
- Supports TLS encryption
- Configurable recipients and subject
- HTML and plain text support

### Webhook Alerts
- Sends HTTP requests to specified URL
- Supports custom headers and methods
- Template-based message formatting
- JSON/XML payload support

### Script Alerts
- Executes custom scripts
- Passes alert message as argument
- Supports custom script arguments
- Captures script output and errors

## Alert Logic
- Pattern matching in log messages
- Threshold-based triggering
- Time window for counting matches
- Cooldown period between alerts

## Message Templates
```yaml
# Email template
email:
  template: |
    Alert: {count} matches in {window} seconds
    Pattern: {pattern}
    Matches:
    {matches}

# Webhook template
webhook:
  template: |
    {{
      "alert": "Log Pattern Match",
      "count": {count},
      "window": {window},
      "pattern": "{pattern}",
      "matches": {matches}
    }}
```

## Example Usage

### Email Alert
```yaml
output:
  type: alert
  channel: "email"
  pattern: "ERROR"
  threshold: 5
  window: 60
  email:
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    username: "alerts@example.com"
    password: "app-password"
    from_addr: "alerts@example.com"
    to_addrs: ["admin@example.com"]
```

### Webhook Alert
```yaml
output:
  type: alert
  channel: "webhook"
  pattern: "ERROR"
  threshold: 5
  window: 60
  webhook:
    url: "https://api.slack.com/webhook"
    method: "POST"
    headers:
      Content-Type: "application/json"
    template: |
      {{
        "text": "Alert: {count} errors in {window}s",
        "attachments": [
          {{
            "text": "Pattern: {pattern}",
            "fields": [
              {{
                "title": "Matches",
                "value": "{matches}",
                "short": false
              }}
            ]
          }}
        ]
      }}
```

### Script Alert
```yaml
output:
  type: alert
  channel: "script"
  pattern: "ERROR"
  threshold: 5
  window: 60
  script:
    path: "/usr/local/bin/alert.sh"
    args: ["--level", "error"]
```

## Installation
```bash
pip install aiohttp
``` 