"""
PostgreSQL output component for PySyslog LFC
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from .base import OutputComponent

# Check for required dependencies
try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

class Output(OutputComponent):
    """PostgreSQL output component for storing logs in a PostgreSQL database.
    
    This component stores log messages in a PostgreSQL database table. It supports
    automatic table creation, batch inserts, and connection pooling.
    
    Dependencies:
        - asyncpg: For PostgreSQL database connectivity
    
    Configuration:
        - host: Database host (required)
        - port: Database port (default: 5432)
        - database: Database name (required)
        - user: Database user (required)
        - password: Database password (required)
        - table: Table name (default: "logs")
        - schema: Custom schema name (optional)
        - batch_size: Number of records to insert in one batch (default: 100)
        - batch_timeout: Maximum time to wait for batch (seconds, default: 1)
        - pool_size: Connection pool size (default: 10)
        - ssl_mode: SSL mode (default: "prefer")
        - create_table: Whether to create table if it doesn't exist (default: True)
        - columns: List of columns to store (default: ["timestamp", "level", "message", "source"])
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize PostgreSQL output.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid or dependencies are missing
        """
        super().__init__(config)
        
        # Check dependencies
        if not ASYNCPG_AVAILABLE:
            raise ValueError(
                "asyncpg module is required for PostgreSQL output. "
                "Please install it using: pip install asyncpg"
            )
        
        # Get configuration with defaults
        self.host = config.get("host")
        self.port = config.get("port", 5432)
        self.database = config.get("database")
        self.user = config.get("user")
        self.password = config.get("password")
        self.table = config.get("table", "logs")
        self.schema = config.get("schema")
        self.batch_size = config.get("batch_size", 100)
        self.batch_timeout = config.get("batch_timeout", 1)
        self.pool_size = config.get("pool_size", 10)
        self.ssl_mode = config.get("ssl_mode", "prefer")
        self.create_table = config.get("create_table", True)
        self.columns = config.get("columns", ["timestamp", "level", "message", "source"])
        
        # Validate configuration
        if not self.host:
            raise ValueError("host parameter is required")
        if not self.database:
            raise ValueError("database parameter is required")
        if not self.user:
            raise ValueError("user parameter is required")
        if not self.password:
            raise ValueError("password parameter is required")
        
        # Initialize connection pool
        self._pool = None
        
        # Initialize batch buffer
        self._batch = []
        self._last_flush = datetime.now()
        
        # Initialize running flag
        self._running = False
    
    async def _create_table(self, conn: asyncpg.Connection):
        """Create table if it doesn't exist.
        
        Args:
            conn: Database connection
        """
        try:
            # Build table name with schema if specified
            table_name = f"{self.schema}.{self.table}" if self.schema else self.table
            
            # Create schema if specified
            if self.schema:
                await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema}")
            
            # Create table
            columns = []
            for col in self.columns:
                if col == "timestamp":
                    columns.append("timestamp TIMESTAMP WITH TIME ZONE")
                elif col == "level":
                    columns.append("level VARCHAR(10)")
                elif col == "message":
                    columns.append("message TEXT")
                elif col == "source":
                    columns.append("source VARCHAR(255)")
                else:
                    columns.append(f"{col} TEXT")
            
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    {", ".join(columns)}
                )
            """)
            
            self.logger.info(f"Created table {table_name}")
            
        except Exception as e:
            self.logger.error(f"Error creating table: {e}", exc_info=True)
            raise
    
    async def _flush_batch(self):
        """Flush batch buffer to database."""
        if not self._batch:
            return
        
        try:
            async with self._pool.acquire() as conn:
                # Build column list
                columns = ["timestamp", "level", "message", "source"]
                if self.schema:
                    table_name = f"{self.schema}.{self.table}"
                else:
                    table_name = self.table
                
                # Build values list
                values = []
                for record in self._batch:
                    value = []
                    for col in columns:
                        value.append(record.get(col))
                    values.append(tuple(value))
                
                # Insert records
                await conn.executemany(f"""
                    INSERT INTO {table_name} ({", ".join(columns)})
                    VALUES ({", ".join(["$" + str(i+1) for i in range(len(columns))])})
                """, values)
                
                self.logger.debug(f"Inserted {len(self._batch)} records")
                
        except Exception as e:
            self.logger.error(f"Error flushing batch: {e}", exc_info=True)
        
        finally:
            # Clear batch
            self._batch = []
            self._last_flush = datetime.now()
    
    async def _check_batch(self):
        """Check if batch should be flushed."""
        now = datetime.now()
        if (len(self._batch) >= self.batch_size or
            (now - self._last_flush).total_seconds() >= self.batch_timeout):
            await self._flush_batch()
    
    async def start(self) -> None:
        """Start the output component."""
        try:
            # Create connection pool
            self._pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=1,
                max_size=self.pool_size,
                ssl=self.ssl_mode != "disable"
            )
            
            # Create table if needed
            if self.create_table:
                async with self._pool.acquire() as conn:
                    await self._create_table(conn)
            
            self._running = True
            self.logger.info("PostgreSQL output started")
            
        except Exception as e:
            self.logger.error(f"Error starting PostgreSQL output: {e}", exc_info=True)
            raise
    
    async def stop(self) -> None:
        """Stop the output component."""
        try:
            self._running = False
            
            # Flush remaining records
            if self._batch:
                await self._flush_batch()
            
            # Close connection pool
            if self._pool:
                await self._pool.close()
            
        except Exception as e:
            self.logger.error(f"Error stopping PostgreSQL output: {e}", exc_info=True)
            raise
    
    async def write(self, data: Dict[str, Any]) -> None:
        """Write log data to database.
        
        Args:
            data: Log data to write
        """
        try:
            # Add to batch
            self._batch.append(data)
            
            # Check if batch should be flushed
            await self._check_batch()
            
        except Exception as e:
            self.logger.error(f"Error writing to PostgreSQL: {e}", exc_info=True)
    
    async def close(self) -> None:
        """Cleanup resources."""
        await self.stop() 