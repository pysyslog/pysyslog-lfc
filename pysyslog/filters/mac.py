"""
MAC address filter component for PySyslog LFC
"""

import logging
import re
from typing import Dict, Any, Callable, Union, List
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on MAC address comparisons.
    
    This filter allows comparing MAC address field values against specified values
    using various operators. It supports MAC address validation, vendor checks,
    and component-based comparisons.
    
    Configuration:
        - field: Field to compare (required)
        - operator: MAC address operator (required)
        - value: MAC address to compare against (required)
        - format: MAC address format (standard, cisco, unix, default: standard)
        - invert: Whether to invert the match (default: False)
    """
    
    # MAC address regex patterns
    MAC_PATTERNS = {
        "standard": re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'),
        "cisco": re.compile(r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})$'),
        "unix": re.compile(r'^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$')
    }
    
    # Valid operators and their functions
    OPERATORS = {
        # MAC address operators
        "equals": lambda x, y: x == y,
        "not_equals": lambda x, y: x != y,
        "contains": lambda x, y: y in x,
        "not_contains": lambda x, y: y not in x,
        
        # Component operators
        "vendor_equals": lambda x, y: x[:6] == y[:6],
        "vendor_not_equals": lambda x, y: x[:6] != y[:6],
        
        # Validation operators
        "is_valid": lambda x, y: bool(x),
        "is_invalid": lambda x, y: not bool(x),
        
        # Special operators
        "is_multicast": lambda x, y: int(x[0:2], 16) & 0x01 == 1,
        "is_broadcast": lambda x, y: x == "ff:ff:ff:ff:ff:ff",
        "is_local": lambda x, y: int(x[0:2], 16) & 0x02 == 2
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize MAC address filter.
        
        Args:
            config: Configuration dictionary containing:
                - field: Field to compare
                - operator: MAC address operator
                - value: MAC address to compare against
                - format: MAC address format (standard, cisco, unix, default: standard)
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
        
        # Get and validate format
        self.format = config.get("format", "standard")
        if self.format not in self.MAC_PATTERNS:
            raise ValueError(f"Invalid format: {self.format}. Must be one of: {', '.join(self.MAC_PATTERNS.keys())}")
        
        # Get and validate value
        self.value = config.get("value")
        if self.value is None:
            raise ValueError("value parameter is required")
        self._validate_string(self.value, "value")
        
        # Validate MAC address format
        if not self.MAC_PATTERNS[self.format].match(self.value):
            raise ValueError(f"Invalid MAC address format: {self.value}")
        
        # Convert to standard format
        self.value = self._normalize_mac(self.value)
        
        # Get operator function
        self._operator_func = self.OPERATORS[self.operator]
    
    def _normalize_mac(self, mac: str) -> str:
        """Normalize MAC address to standard format.
        
        Args:
            mac: MAC address to normalize
            
        Returns:
            Normalized MAC address
        """
        # Remove separators
        mac = re.sub(r'[.:-]', '', mac)
        
        # Convert to standard format
        return ':'.join(mac[i:i+2] for i in range(0, len(mac), 2))
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on MAC address comparison.
        
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
            
            # Validate format
            if not self.MAC_PATTERNS[self.format].match(field_value):
                return False
            
            # Normalize MAC address
            field_value = self._normalize_mac(field_value)
            
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