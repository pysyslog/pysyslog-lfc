"""
Protocol filter component for PySyslog LFC
"""

import logging
from typing import Dict, Any, Callable, Union, List
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on protocol comparisons.
    
    This filter allows comparing protocol field values against specified values
    using various operators. It supports protocol validation, layer checks,
    and common protocol comparisons.
    
    Configuration:
        - field: Field to compare (required)
        - operator: Protocol operator (required)
        - value: Protocol to compare against (required)
        - invert: Whether to invert the match (default: False)
    """
    
    # Protocol layers
    PROTOCOL_LAYERS = {
        "application": ["http", "https", "ftp", "smtp", "pop3", "imap", "dns", "ssh", "telnet", "mysql", "postgresql", "redis", "mongodb"],
        "transport": ["tcp", "udp", "sctp"],
        "network": ["ipv4", "ipv6", "icmp", "icmpv6"],
        "data_link": ["ethernet", "ppp", "pppoe"],
        "physical": ["wifi", "bluetooth", "zigbee"]
    }
    
    # Common protocols with their default ports
    COMMON_PROTOCOLS = {
        # Application layer
        "http": 80,
        "https": 443,
        "ftp": 21,
        "smtp": 25,
        "pop3": 110,
        "imap": 143,
        "dns": 53,
        "ssh": 22,
        "telnet": 23,
        "mysql": 3306,
        "postgresql": 5432,
        "redis": 6379,
        "mongodb": 27017,
        
        # Transport layer
        "tcp": 6,
        "udp": 17,
        "sctp": 132,
        
        # Network layer
        "ipv4": 4,
        "ipv6": 41,
        "icmp": 1,
        "icmpv6": 58,
        
        # Data link layer
        "ethernet": 1,
        "ppp": 0x880B,
        "pppoe": 0x8864,
        
        # Physical layer
        "wifi": 0x88C0,
        "bluetooth": 0x0003,
        "zigbee": 0x0041
    }
    
    # Valid operators and their functions
    OPERATORS = {
        # Protocol operators
        "equals": lambda x, y: x == y,
        "not_equals": lambda x, y: x != y,
        "contains": lambda x, y: y in x,
        "not_contains": lambda x, y: y not in x,
        
        # Layer operators
        "in_layer": lambda x, y: x in Filter.PROTOCOL_LAYERS[y],
        "not_in_layer": lambda x, y: x not in Filter.PROTOCOL_LAYERS[y],
        
        # Validation operators
        "is_valid": lambda x, y: bool(x),
        "is_invalid": lambda x, y: not bool(x),
        
        # Special operators
        "is_secure": lambda x, y: x in ["https", "ssh", "smtp_submit", "imap_ssl", "pop3_ssl"],
        "is_unsecure": lambda x, y: x in ["http", "telnet", "ftp", "smtp", "imap", "pop3"]
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize protocol filter.
        
        Args:
            config: Configuration dictionary containing:
                - field: Field to compare
                - operator: Protocol operator
                - value: Protocol to compare against
                - invert: Whether to invert the match (default: False)
                
        Raises:
            ValueError: If configuration is invalid
        """
        super().__init__(config)
        
        # Get and validate field
        self.field = config.get("field")
        if not self.field:
            raise ValueError("field parameter is required")
        self._validate_string(self.field, "field")
        
        # Get and validate operator
        self.operator = config.get("operator")
        if not self.operator:
            raise ValueError("operator parameter is required")
        if self.operator not in self.OPERATORS:
            raise ValueError(f"Invalid operator: {self.operator}. Must be one of: {', '.join(self.OPERATORS.keys())}")
        
        # Get and validate value
        self.value = config.get("value")
        if self.value is None:
            raise ValueError("value parameter is required")
        self._validate_string(self.value, "value")
        
        # Validate protocol if needed
        if self.operator in ["in_layer", "not_in_layer"]:
            if self.value not in self.PROTOCOL_LAYERS:
                raise ValueError(f"Invalid protocol layer: {self.value}")
        elif self.operator not in ["is_valid", "is_invalid"]:
            if self.value not in self.COMMON_PROTOCOLS:
                raise ValueError(f"Invalid protocol: {self.value}")
        
        # Get operator function
        self._operator_func = self.OPERATORS[self.operator]
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on protocol comparison.
        
        Args:
            data: Parsed message data
            
        Returns:
            bool: True if message should be kept, False if filtered out
        """
        try:
            # Get field value
            field_value = data.get(self.field)
            if field_value is None:
                return False
            
            # Convert to string if needed
            if not isinstance(field_value, str):
                field_value = str(field_value)
            
            # Convert to lowercase
            field_value = field_value.lower()
            
            # Apply operator
            result = self._operator_func(field_value, self.value)
            
            # Apply invert if specified
            if self.invert:
                result = not result
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error filtering message: {e}", exc_info=True)
            return False
    
    def close(self) -> None:
        """Cleanup resources."""
        pass 