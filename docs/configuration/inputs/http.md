# HTTP Input Component

The HTTP input component allows receiving log messages via HTTP endpoints. It supports authentication, rate limiting, and SSL/TLS encryption.

## Dependencies
- `aiohttp`: For HTTP server functionality
- `ssl`: For SSL/TLS support (built-in)

## Configuration
```yaml
input:
  type: http
  host: "0.0.0.0"          # Host to bind to
  port: 8080               # Port to listen on
  endpoints: ["/logs"]     # List of endpoints to expose
  auth_type: "basic"       # Authentication type (basic or api_key)
  username: "user"         # Username for basic auth
  password: "pass"         # Password for basic auth
  api_key: "secret"        # API key for API key auth
  rate_limit: 100          # Rate limit per IP (requests/second)
  ssl_cert: "/path/cert"   # Path to SSL certificate
  ssl_key: "/path/key"     # Path to SSL private key
  max_request_size: 10485760  # Maximum request size (10MB default)
```

## Authentication Methods

### Basic Authentication
- Uses standard HTTP Basic Auth
- Requires username and password
- Credentials sent in Authorization header

### API Key Authentication
- Uses X-API-Key header
- Requires API key configuration
- More suitable for service-to-service communication

## Security Features
- Rate limiting per IP address
- SSL/TLS encryption support
- Request size limits
- Input validation
- Secure credential handling

## Example Usage
```bash
# Send log via curl with basic auth
curl -X POST http://localhost:8080/logs \
  -u user:pass \
  -H "Content-Type: application/json" \
  -d '{"message": "Test log"}'

# Send log via curl with API key
curl -X POST http://localhost:8080/logs \
  -H "X-API-Key: secret" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test log"}'
```

## Error Handling
- 401: Unauthorized (invalid credentials)
- 413: Request Entity Too Large
- 429: Too Many Requests (rate limit exceeded)
- 400: Bad Request (invalid input)
- 500: Internal Server Error

## Installation
```bash
pip install aiohttp
``` 