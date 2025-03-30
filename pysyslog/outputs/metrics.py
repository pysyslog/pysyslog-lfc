"""
Metrics output component for PySyslog LFC
"""

import logging
import asyncio
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
    """Metrics output component for exporting log-based metrics.
    
    This component exports metrics based on log messages. It supports multiple
    metric types including counters, gauges, and histograms, and can export
    them in various formats including Prometheus and custom HTTP endpoints.
    
    Dependencies:
        - aiohttp: For HTTP server and client functionality
    
    Configuration:
        - format: Metric format ("prometheus" or "custom")
        - interval: Export interval in seconds (default: 15)
        - metrics:
            - name: Metric name
            - type: Metric type ("counter", "gauge", or "histogram")
            - pattern: Regex pattern to match
            - labels: List of label names to extract
            - value: Value to use (default: 1 for counters)
            - buckets: List of histogram buckets
        - prometheus:
            - port: Port to expose metrics (default: 9090)
            - path: Metrics path (default: "/metrics")
        - custom:
            - url: HTTP endpoint URL
            - method: HTTP method (default: "POST")
            - headers: Custom HTTP headers
            - template: Metric format template
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize metrics output.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid or dependencies are missing
        """
        super().__init__(config)
        
        # Check dependencies
        if not AIOHTTP_AVAILABLE:
            raise ValueError(
                "aiohttp module is required for metrics output. "
                "Please install it using: pip install aiohttp"
            )
        
        # Get configuration with defaults
        self.format = config.get("format")
        self.interval = config.get("interval", 15)
        self.metrics = config.get("metrics", [])
        
        # Validate format
        if not self.format or self.format not in ["prometheus", "custom"]:
            raise ValueError("format must be 'prometheus' or 'custom'")
        
        # Validate metrics
        if not self.metrics:
            raise ValueError("metrics list is required")
        
        for metric in self.metrics:
            if "name" not in metric:
                raise ValueError("metric.name is required")
            if "type" not in metric or metric["type"] not in ["counter", "gauge", "histogram"]:
                raise ValueError("metric.type must be 'counter', 'gauge', or 'histogram'")
            if "pattern" not in metric:
                raise ValueError("metric.pattern is required")
            
            metric["labels"] = metric.get("labels", [])
            metric["value"] = metric.get("value", 1)
            metric["buckets"] = metric.get("buckets", [])
        
        # Get format-specific configuration
        self.format_config = config.get(self.format, {})
        
        # Validate format configuration
        if self.format == "prometheus":
            self._validate_prometheus_config()
        elif self.format == "custom":
            self._validate_custom_config()
        
        # Initialize metric storage
        self._counters = {}
        self._gauges = {}
        self._histograms = {}
        
        # Initialize running flag
        self._running = False
    
    def _validate_prometheus_config(self):
        """Validate Prometheus configuration."""
        self.format_config["port"] = self.format_config.get("port", 9090)
        self.format_config["path"] = self.format_config.get("path", "/metrics")
    
    def _validate_custom_config(self):
        """Validate custom configuration."""
        if "url" not in self.format_config:
            raise ValueError("custom.url is required")
        
        self.format_config["method"] = self.format_config.get("method", "POST")
        self.format_config["headers"] = self.format_config.get("headers", {})
        self.format_config["template"] = self.format_config.get("template", "{metrics}")
    
    def _get_metric_key(self, metric: Dict[str, Any], labels: Dict[str, str]) -> str:
        """Get metric key with labels.
        
        Args:
            metric: Metric configuration
            labels: Label values
            
        Returns:
            Metric key
        """
        key = metric["name"]
        if labels:
            label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
            key = f"{key}{{{label_str}}}"
        return key
    
    def _update_counter(self, metric: Dict[str, Any], labels: Dict[str, str], value: float):
        """Update counter metric.
        
        Args:
            metric: Metric configuration
            labels: Label values
            value: Metric value
        """
        key = self._get_metric_key(metric, labels)
        if key not in self._counters:
            self._counters[key] = 0
        self._counters[key] += value
    
    def _update_gauge(self, metric: Dict[str, Any], labels: Dict[str, str], value: float):
        """Update gauge metric.
        
        Args:
            metric: Metric configuration
            labels: Label values
            value: Metric value
        """
        key = self._get_metric_key(metric, labels)
        self._gauges[key] = value
    
    def _update_histogram(self, metric: Dict[str, Any], labels: Dict[str, str], value: float):
        """Update histogram metric.
        
        Args:
            metric: Metric configuration
            labels: Label values
            value: Metric value
        """
        key = self._get_metric_key(metric, labels)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)
    
    def _format_prometheus(self) -> str:
        """Format metrics in Prometheus format.
        
        Returns:
            Formatted metrics
        """
        lines = []
        
        # Format counters
        for key, value in self._counters.items():
            lines.append(f"{key} {value}")
        
        # Format gauges
        for key, value in self._gauges.items():
            lines.append(f"{key} {value}")
        
        # Format histograms
        for key, values in self._histograms.items():
            for bucket in self.metrics[0]["buckets"]:
                count = sum(1 for v in values if v <= bucket)
                lines.append(f"{key}_bucket{{le=\"{bucket}\"}} {count}")
            lines.append(f"{key}_sum {sum(values)}")
            lines.append(f"{key}_count {len(values)}")
        
        return "\n".join(lines)
    
    def _format_custom(self) -> str:
        """Format metrics in custom format.
        
        Returns:
            Formatted metrics
        """
        metrics = {
            "counters": self._counters,
            "gauges": self._gauges,
            "histograms": self._histograms
        }
        
        template = self.format_config["template"]
        return template.format(metrics=metrics)
    
    async def _export_metrics(self):
        """Export metrics."""
        try:
            if self.format == "prometheus":
                # Format metrics
                metrics = self._format_prometheus()
                
                # Send response
                self._response_text = metrics
                
            elif self.format == "custom":
                # Format metrics
                metrics = self._format_custom()
                
                # Send request
                url = self.format_config["url"]
                method = self.format_config["method"]
                headers = self.format_config["headers"]
                
                async with aiohttp.ClientSession() as session:
                    async with session.request(method, url, headers=headers, data=metrics) as response:
                        if response.status >= 400:
                            raise Exception(f"Custom export failed with status {response.status}")
                
                self.logger.info("Metrics exported")
            
        except Exception as e:
            self.logger.error(f"Error exporting metrics: {e}", exc_info=True)
    
    async def _handle_request(self, request: aiohttp.web.Request) -> aiohttp.web.Response:
        """Handle Prometheus metrics request.
        
        Args:
            request: HTTP request object
            
        Returns:
            HTTP response object
        """
        return aiohttp.web.Response(text=self._response_text)
    
    async def _start_server(self):
        """Start Prometheus metrics server."""
        try:
            # Create application
            app = aiohttp.web.Application()
            
            # Add route
            app.router.add_get(self.format_config["path"], self._handle_request)
            
            # Create server
            self._server = await aiohttp.web._run_app(
                app,
                host="0.0.0.0",
                port=self.format_config["port"]
            )
            
            self.logger.info(f"Prometheus metrics server started on port {self.format_config['port']}")
            
        except Exception as e:
            self.logger.error(f"Error starting Prometheus metrics server: {e}", exc_info=True)
            raise
    
    async def start(self) -> None:
        """Start the output component."""
        try:
            if self.format == "prometheus":
                # Start server
                await self._start_server()
            
            self._running = True
            self.logger.info("Metrics output started")
            
        except Exception as e:
            self.logger.error(f"Error starting metrics output: {e}", exc_info=True)
            raise
    
    async def stop(self) -> None:
        """Stop the output component."""
        try:
            self._running = False
            
            if self.format == "prometheus" and self._server:
                await self._server.shutdown()
                await self._server.cleanup()
            
        except Exception as e:
            self.logger.error(f"Error stopping metrics output: {e}", exc_info=True)
            raise
    
    async def write(self, data: Dict[str, Any]) -> None:
        """Write log data and update metrics.
        
        Args:
            data: Log data to write
        """
        try:
            # Get message
            message = data.get("message", "")
            
            # Update metrics
            for metric in self.metrics:
                # Check pattern
                if metric["pattern"] in message:
                    # Extract labels
                    labels = {}
                    for label in metric["labels"]:
                        if label in data:
                            labels[label] = str(data[label])
                    
                    # Update metric
                    if metric["type"] == "counter":
                        self._update_counter(metric, labels, metric["value"])
                    elif metric["type"] == "gauge":
                        self._update_gauge(metric, labels, metric["value"])
                    elif metric["type"] == "histogram":
                        self._update_histogram(metric, labels, metric["value"])
            
        except Exception as e:
            self.logger.error(f"Error in metrics output: {e}", exc_info=True)
    
    async def close(self) -> None:
        """Cleanup resources."""
        await self.stop() 