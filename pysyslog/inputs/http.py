"""
HTTP input component for PySyslog LFC
"""

import logging
import asyncio
import ssl
from typing import Dict, Any, Optional
from .base import InputComponent

# Check for required dependencies
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

class Input(InputComponent):
    """HTTP input component for receiving logs via HTTP endpoints.
    
    This component listens for log messages on HTTP endpoints and forwards them
    to the message queue. It supports basic authentication, API key authentication,
    and rate limiting.
    
    Dependencies:
        - aiohttp: For HTTP server functionality
        - ssl: For SSL/TLS support (built-in)
    
    Configuration:
        - host: Host to bind to (default: "0.0.0.0")
        - port: Port to listen on (default: 8080)
        - endpoints: List of endpoints to expose (default: ["/logs"])
        - auth_type: Authentication type ("basic" or "api_key")
        - username: Username for basic auth
        - password: Password for basic auth
        - api_key: API key for API key auth
        - rate_limit: Rate limit per IP (requests per second)
        - ssl_cert: Path to SSL certificate file
        - ssl_key: Path to SSL private key file
        - max_request_size: Maximum request size in bytes
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize HTTP input.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid or dependencies are missing
        """
        super().__init__(config)
        
        # Check dependencies
        if not AIOHTTP_AVAILABLE:
            raise ValueError(
                "aiohttp module is required for HTTP input. "
                "Please install it using: pip install aiohttp"
            )
        
        # Get configuration with defaults
        self.host = config.get("host", "0.0.0.0")
        self.port = config.get("port", 8080)
        self.endpoints = config.get("endpoints", ["/logs"])
        self.auth_type = config.get("auth_type")
        self.username = config.get("username")
        self.password = config.get("password")
        self.api_key = config.get("api_key")
        self.rate_limit = config.get("rate_limit")
        self.ssl_cert = config.get("ssl_cert")
        self.ssl_key = config.get("ssl_key")
        self.max_request_size = config.get("max_request_size", 10 * 1024 * 1024)  # 10MB default
        
        # Validate configuration
        if self.auth_type and self.auth_type not in ["basic", "api_key"]:
            raise ValueError("auth_type must be 'basic' or 'api_key'")
        
        if self.auth_type == "basic" and (not self.username or not self.password):
            raise ValueError("username and password required for basic auth")
        
        if self.auth_type == "api_key" and not self.api_key:
            raise ValueError("api_key required for API key auth")
        
        if self.ssl_cert and not self.ssl_key:
            raise ValueError("ssl_key required when using ssl_cert")
        
        # Initialize rate limiting
        self._rate_limits = {}
        
        # Initialize server
        self._server = None
        self._running = False
    
    async def _handle_request(self, request: aiohttp.web.Request) -> aiohttp.web.Response:
        """Handle incoming HTTP request.
        
        Args:
            request: HTTP request object
            
        Returns:
            HTTP response object
        """
        try:
            # Check rate limit
            if self.rate_limit:
                client_ip = request.remote
                if client_ip in self._rate_limits:
                    if self._rate_limits[client_ip] >= self.rate_limit:
                        return aiohttp.web.Response(status=429, text="Too Many Requests")
                    self._rate_limits[client_ip] += 1
                else:
                    self._rate_limits[client_ip] = 1
            
            # Check authentication
            if self.auth_type == "basic":
                auth_header = request.headers.get("Authorization")
                if not auth_header or not auth_header.startswith("Basic "):
                    return aiohttp.web.Response(status=401, text="Unauthorized")
                
                import base64
                try:
                    credentials = base64.b64decode(auth_header[6:]).decode()
                    username, password = credentials.split(":", 1)
                    if username != self.username or password != self.password:
                        return aiohttp.web.Response(status=401, text="Unauthorized")
                except:
                    return aiohttp.web.Response(status=401, text="Unauthorized")
            
            elif self.auth_type == "api_key":
                api_key = request.headers.get("X-API-Key")
                if not api_key or api_key != self.api_key:
                    return aiohttp.web.Response(status=401, text="Unauthorized")
            
            # Check request size
            content_length = request.content_length
            if content_length and content_length > self.max_request_size:
                return aiohttp.web.Response(status=413, text="Request Entity Too Large")
            
            # Read request body
            try:
                body = await request.read()
                if not body:
                    return aiohttp.web.Response(status=400, text="Empty Request Body")
            except Exception as e:
                self.logger.error(f"Error reading request body: {e}")
                return aiohttp.web.Response(status=400, text="Invalid Request Body")
            
            # Forward message to queue
            await self.queue.put(body)
            
            return aiohttp.web.Response(status=200, text="OK")
            
        except Exception as e:
            self.logger.error(f"Error handling request: {e}", exc_info=True)
            return aiohttp.web.Response(status=500, text="Internal Server Error")
    
    async def _start_server(self):
        """Start HTTP server."""
        try:
            # Create application
            app = aiohttp.web.Application()
            
            # Add routes
            for endpoint in self.endpoints:
                app.router.add_post(endpoint, self._handle_request)
            
            # Create server
            if self.ssl_cert and self.ssl_key:
                ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ssl_context.load_cert_chain(self.ssl_cert, self.ssl_key)
                self._server = await aiohttp.web._run_app(app, host=self.host, port=self.port, ssl_context=ssl_context)
            else:
                self._server = await aiohttp.web._run_app(app, host=self.host, port=self.port)
            
            self._running = True
            self.logger.info(f"HTTP server started on {self.host}:{self.port}")
            
        except Exception as e:
            self.logger.error(f"Error starting HTTP server: {e}", exc_info=True)
            raise
    
    async def start(self) -> None:
        """Start the input component."""
        try:
            # Start server
            await self._start_server()
            
            # Keep running
            while self._running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Error in HTTP input: {e}", exc_info=True)
            raise
    
    async def stop(self) -> None:
        """Stop the input component."""
        try:
            self._running = False
            if self._server:
                await self._server.shutdown()
                await self._server.cleanup()
            
        except Exception as e:
            self.logger.error(f"Error stopping HTTP input: {e}", exc_info=True)
            raise
    
    async def close(self) -> None:
        """Cleanup resources."""
        await self.stop() 