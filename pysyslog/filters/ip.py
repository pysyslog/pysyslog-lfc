"""
IP address filter component for PySyslog LFC
"""

import logging
import ipaddress
from typing import Dict, Any, Callable, Union, List
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on IP address comparisons.
    
    This filter allows comparing IP address field values against specified values
    using various operators. It supports IPv4 and IPv6 addresses, CIDR ranges,
    and network membership checks.
    
    Configuration:
        - field: Field to compare (required)
        - operator: IP address operator (required)
        - value: IP address or CIDR range to compare against (required)
        - invert: Whether to invert the match (default: False)
    """
    
    # Valid operators and their functions
    OPERATORS = {
        "equals": lambda x, y: x == y,
        "not_equals": lambda x, y: x != y,
        "in_network": lambda x, y: x in y,
        "not_in_network": lambda x, y: x not in y,
        "is_private": lambda x, y: x.is_private,
        "is_global": lambda x, y: x.is_global,
        "is_multicast": lambda x, y: x.is_multicast,
        "is_loopback": lambda x, y: x.is_loopback,
        "is_link_local": lambda x, y: x.is_link_local
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize IP address filter.
        
        Args:
            config: Configuration dictionary containing:
                - field: Field to compare
                - operator: IP address operator
                - value: IP address or CIDR range to compare against
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
            
        # Parse value based on operator
        if self.operator in ["in_network", "not_in_network"]:
            try:
                self.value = ipaddress.ip_network(self.value)
            except ValueError as e:
                raise ValueError(f"Invalid CIDR range: {e}")
        else:
            try:
                self.value = ipaddress.ip_address(self.value)
            except ValueError as e:
                raise ValueError(f"Invalid IP address: {e}")
        
        # Get operator function
        self._operator_func = self.OPERATORS[self.operator]
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on IP address comparison.
        
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
            
            # Convert to IP address
            try:
                field_value = ipaddress.ip_address(field_value)
            except ValueError:
                return False
            
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