"""
URL filter component for PySyslog LFC
"""

import logging
from urllib.parse import urlparse, urlunparse
from typing import Dict, Any, Callable, Union, List
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on URL comparisons.
    
    This filter allows comparing URL field values against specified values
    using various operators. It supports URL parsing, validation, and
    component-based comparisons.
    
    Configuration:
        - field: Field to compare (required)
        - operator: URL operator (required)
        - value: URL or URL component to compare against (required)
        - component: URL component to compare (optional)
        - invert: Whether to invert the match (default: False)
    """
    
    # Valid operators and their functions
    OPERATORS = {
        # URL operators
        "equals": lambda x, y: x == y,
        "not_equals": lambda x, y: x != y,
        "contains": lambda x, y: y in x,
        "not_contains": lambda x, y: y not in x,
        "startswith": lambda x, y: x.startswith(y),
        "endswith": lambda x, y: x.endswith(y),
        
        # Component operators
        "scheme_equals": lambda x, y: x.scheme == y,
        "netloc_equals": lambda x, y: x.netloc == y,
        "path_equals": lambda x, y: x.path == y,
        "query_equals": lambda x, y: x.query == y,
        "fragment_equals": lambda x, y: x.fragment == y,
        
        # Validation operators
        "is_valid": lambda x, y: bool(x.scheme and x.netloc),
        "is_secure": lambda x, y: x.scheme in ["https", "wss"],
        "is_absolute": lambda x, y: bool(x.scheme),
        "is_relative": lambda x, y: not x.scheme
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize URL filter.
        
        Args:
            config: Configuration dictionary containing:
                - field: Field to compare
                - operator: URL operator
                - value: URL or URL component to compare against
                - component: URL component to compare (optional)
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
        
        # Parse value if it's a URL
        if self.operator in ["scheme_equals", "netloc_equals", "path_equals", 
                           "query_equals", "fragment_equals", "is_valid",
                           "is_secure", "is_absolute", "is_relative"]:
            try:
                self.value = urlparse(self.value)
            except Exception as e:
                raise ValueError(f"Invalid URL: {e}")
        
        # Get operator function
        self._operator_func = self.OPERATORS[self.operator]
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on URL comparison.
        
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
            
            # Parse URL if needed
            if self.operator in ["scheme_equals", "netloc_equals", "path_equals", 
                               "query_equals", "fragment_equals", "is_valid",
                               "is_secure", "is_absolute", "is_relative"]:
                try:
                    field_value = urlparse(field_value)
                except Exception:
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