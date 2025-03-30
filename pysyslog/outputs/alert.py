"""
Alert output component for PySyslog LFC
"""

import logging
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from .base import OutputComponent

# Check for required dependencies
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

class Output(OutputComponent):
    """Alert output component for sending alerts based on log patterns.
    
    This component sends alerts when log messages match specified patterns.
    It supports multiple notification channels including email, HTTP webhooks,
    and custom scripts.
    
    Dependencies:
        - aiohttp: For HTTP webhook functionality
        - smtplib: For email functionality (built-in)
    
    Configuration:
        - channel: Alert channel ("email", "webhook", or "script")
        - pattern: Regex pattern to match
        - threshold: Number of matches before alert (default: 1)
        - window: Time window for threshold in seconds (default: 60)
        - cooldown: Minimum time between alerts in seconds (default: 300)
        - email:
            - smtp_host: SMTP server host
            - smtp_port: SMTP server port
            - username: SMTP username
            - password: SMTP password
            - from_addr: From email address
            - to_addrs: List of recipient email addresses
            - subject: Email subject
        - webhook:
            - url: Webhook URL
            - method: HTTP method (default: "POST")
            - headers: Custom HTTP headers
            - template: Alert message template
        - script:
            - path: Path to alert script
            - args: List of script arguments
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize alert output.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid or dependencies are missing
        """
        super().__init__(config)
        
        # Check dependencies
        if config.get("channel") == "webhook" and not AIOHTTP_AVAILABLE:
            raise ValueError(
                "aiohttp module is required for webhook alerts. "
                "Please install it using: pip install aiohttp"
            )
        
        # Get configuration with defaults
        self.channel = config.get("channel")
        self.pattern = config.get("pattern")
        self.threshold = config.get("threshold", 1)
        self.window = config.get("window", 60)
        self.cooldown = config.get("cooldown", 300)
        
        # Validate channel
        if not self.channel or self.channel not in ["email", "webhook", "script"]:
            raise ValueError("channel must be 'email', 'webhook', or 'script'")
        
        # Validate pattern
        if not self.pattern:
            raise ValueError("pattern parameter is required")
        
        # Get channel-specific configuration
        self.channel_config = config.get(self.channel, {})
        
        # Validate channel configuration
        if self.channel == "email":
            self._validate_email_config()
        elif self.channel == "webhook":
            self._validate_webhook_config()
        elif self.channel == "script":
            self._validate_script_config()
        
        # Initialize alert tracking
        self._matches = []
        self._last_alert = None
        
        # Initialize running flag
        self._running = False
    
    def _validate_email_config(self):
        """Validate email configuration."""
        required = ["smtp_host", "smtp_port", "username", "password", "from_addr", "to_addrs"]
        for param in required:
            if param not in self.channel_config:
                raise ValueError(f"email.{param} is required")
        
        if not isinstance(self.channel_config["to_addrs"], list):
            raise ValueError("email.to_addrs must be a list")
    
    def _validate_webhook_config(self):
        """Validate webhook configuration."""
        if "url" not in self.channel_config:
            raise ValueError("webhook.url is required")
        
        self.channel_config["method"] = self.channel_config.get("method", "POST")
        self.channel_config["headers"] = self.channel_config.get("headers", {})
        self.channel_config["template"] = self.channel_config.get("template", "{message}")
    
    def _validate_script_config(self):
        """Validate script configuration."""
        if "path" not in self.channel_config:
            raise ValueError("script.path is required")
        
        self.channel_config["args"] = self.channel_config.get("args", [])
    
    async def _send_email_alert(self, message: str):
        """Send email alert.
        
        Args:
            message: Alert message
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.channel_config["from_addr"]
            msg["To"] = ", ".join(self.channel_config["to_addrs"])
            msg["Subject"] = self.channel_config.get("subject", "Log Alert")
            
            msg.attach(MIMEText(message, "plain"))
            
            # Send email
            with smtplib.SMTP(self.channel_config["smtp_host"], self.channel_config["smtp_port"]) as server:
                server.starttls()
                server.login(self.channel_config["username"], self.channel_config["password"])
                server.send_message(msg)
            
            self.logger.info("Email alert sent")
            
        except Exception as e:
            self.logger.error(f"Error sending email alert: {e}", exc_info=True)
    
    async def _send_webhook_alert(self, message: str):
        """Send webhook alert.
        
        Args:
            message: Alert message
        """
        try:
            # Prepare request
            url = self.channel_config["url"]
            method = self.channel_config["method"]
            headers = self.channel_config["headers"]
            template = self.channel_config["template"]
            
            # Format message
            formatted_message = template.format(message=message)
            
            # Send request
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, headers=headers, data=formatted_message) as response:
                    if response.status >= 400:
                        raise Exception(f"Webhook request failed with status {response.status}")
            
            self.logger.info("Webhook alert sent")
            
        except Exception as e:
            self.logger.error(f"Error sending webhook alert: {e}", exc_info=True)
    
    async def _send_script_alert(self, message: str):
        """Send script alert.
        
        Args:
            message: Alert message
        """
        try:
            # Prepare command
            cmd = [self.channel_config["path"]] + self.channel_config["args"]
            
            # Add message as last argument
            cmd.append(message)
            
            # Run script
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Script failed with return code {process.returncode}: {stderr.decode()}")
            
            self.logger.info("Script alert sent")
            
        except Exception as e:
            self.logger.error(f"Error sending script alert: {e}", exc_info=True)
    
    async def _check_threshold(self):
        """Check if alert threshold is reached."""
        now = datetime.now()
        
        # Remove old matches
        self._matches = [t for t in self._matches if (now - t).total_seconds() <= self.window]
        
        # Check threshold
        if len(self._matches) >= self.threshold:
            # Check cooldown
            if self._last_alert and (now - self._last_alert).total_seconds() < self.cooldown:
                return
            
            # Send alert
            message = f"Alert: {len(self._matches)} matches in {self.window} seconds"
            
            if self.channel == "email":
                await self._send_email_alert(message)
            elif self.channel == "webhook":
                await self._send_webhook_alert(message)
            elif self.channel == "script":
                await self._send_script_alert(message)
            
            self._last_alert = now
    
    async def start(self) -> None:
        """Start the output component."""
        self._running = True
        self.logger.info("Alert output started")
    
    async def stop(self) -> None:
        """Stop the output component."""
        self._running = False
    
    async def write(self, data: Dict[str, Any]) -> None:
        """Write log data and check for alerts.
        
        Args:
            data: Log data to write
        """
        try:
            # Check if message matches pattern
            message = data.get("message", "")
            if self.pattern in message:
                self._matches.append(datetime.now())
                await self._check_threshold()
            
        except Exception as e:
            self.logger.error(f"Error in alert output: {e}", exc_info=True)
    
    async def close(self) -> None:
        """Cleanup resources."""
        await self.stop() 