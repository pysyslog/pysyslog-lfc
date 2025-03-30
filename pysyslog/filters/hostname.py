"""
Hostname filter component for PySyslog LFC
"""

import logging
import re
from typing import Dict, Any, Callable, Union, List
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on hostname comparisons.
    
    This filter allows comparing hostname field values against specified values
    using various operators. It supports hostname validation, domain checks,
    and component-based comparisons.
    
    Configuration:
        - field: Field to compare (required)
        - operator: Hostname operator (required)
        - value: Hostname or hostname component to compare against (required)
        - component: Hostname component to compare (optional)
        - invert: Whether to invert the match (default: False)
    """
    
    # Hostname regex pattern
    HOSTNAME_PATTERN = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$')
    
    # Valid operators and their functions
    OPERATORS = {
        # Hostname operators
        "equals": lambda x, y: x == y,
        "not_equals": lambda x, y: x != y,
        "contains": lambda x, y: y in x,
        "not_contains": lambda x, y: y not in x,
        "startswith": lambda x, y: x.startswith(y),
        "endswith": lambda x, y: x.endswith(y),
        
        # Component operators
        "domain_equals": lambda x, y: x.split(".")[-2:] == y.split("."),
        "domain_ends_with": lambda x, y: x.endswith(y),
        "subdomain_equals": lambda x, y: x.split(".")[0] == y,
        
        # Validation operators
        "is_valid": lambda x, y: bool(Filter.HOSTNAME_PATTERN.match(x)),
        "is_invalid": lambda x, y: not bool(Filter.HOSTNAME_PATTERN.match(x)),
        
        # Special operators
        "is_ipv4": lambda x, y: bool(re.match(r'^(\d{1,3}\.){3}\d{1,3}$', x)),
        "is_ipv6": lambda x, y: bool(re.match(r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$', x)),
        "is_localhost": lambda x, y: x.lower() in ["localhost", "127.0.0.1", "::1"]
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize hostname filter.
        
        Args:
            config: Configuration dictionary containing:
                - field: Field to compare
                - operator: Hostname operator
                - value: Hostname or hostname component to compare against
                - component: Hostname component to compare (optional)
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
        
        # Validate hostname if needed
        if self.operator in ["domain_equals", "domain_ends_with", "subdomain_equals"]:
            if not self.HOSTNAME_PATTERN.match(self.value):
                raise ValueError(f"Invalid hostname: {self.value}")
        
        # Get operator function
        self._operator_func = self.OPERATORS[self.operator]
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on hostname comparison.
        
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