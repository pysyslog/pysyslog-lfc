# PostgreSQL Output Component

The PostgreSQL output component stores log messages in a PostgreSQL database. It supports automatic table creation, batch inserts, and connection pooling.

## Dependencies
- `asyncpg`: For PostgreSQL database connectivity

## Configuration
```yaml
output:
  type: postgresql
  host: "localhost"        # Database host
  port: 5432              # Database port
  database: "logs"        # Database name
  user: "postgres"        # Database user
  password: "secret"      # Database password
  table: "logs"           # Table name
  schema: "public"        # Custom schema name
  batch_size: 100         # Records per batch
  batch_timeout: 1        # Batch timeout (seconds)
  pool_size: 10           # Connection pool size
  ssl_mode: "prefer"      # SSL mode
  create_table: true      # Auto-create table
  columns:                # Columns to store
    - timestamp
    - level
    - message
    - source
```

## Table Schema
```sql
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE,
    level VARCHAR(10),
    message TEXT,
    source VARCHAR(255)
);
```

## Features
- Automatic table creation
- Batch inserts for better performance
- Connection pooling
- SSL support
- Custom schema support
- Configurable columns

## Performance Considerations
- Batch size affects memory usage and insert performance
- Pool size should match expected concurrent connections
- Batch timeout helps balance latency and throughput

## SSL Modes
- `disable`: No SSL
- `allow`: Try SSL, fall back to non-SSL
- `prefer`: Try SSL, fall back to non-SSL (default)
- `require`: Always use SSL
- `verify-ca`: Always use SSL and verify server certificate
- `verify-full`: Always use SSL and verify server certificate and hostname

## Example Queries
```sql
-- Count errors by source
SELECT source, COUNT(*) as error_count
FROM logs
WHERE level = 'ERROR'
GROUP BY source;

-- Get recent errors
SELECT timestamp, source, message
FROM logs
WHERE level = 'ERROR'
ORDER BY timestamp DESC
LIMIT 100;
```

## Installation
```bash
pip install asyncpg
``` 