"""
Path filter component for PySyslog LFC
"""

import logging
import os
import re
from typing import Dict, Any, Callable, Union, List
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on file path comparisons.
    
    This filter allows comparing file path field values against specified values
    using various operators. It supports path validation, component checks,
    and file system operations.
    
    Configuration:
        - field: Field to compare (required)
        - operator: Path operator (required)
        - value: Path or path component to compare against (required)
        - component: Path component to compare (optional)
        - invert: Whether to invert the match (default: False)
    """
    
    # Path regex pattern
    PATH_PATTERN = re.compile(r'^[a-zA-Z0-9\-_\./\\]+$')
    
    # Valid operators and their functions
    OPERATORS = {
        # Path operators
        "equals": lambda x, y: x == y,
        "not_equals": lambda x, y: x != y,
        "contains": lambda x, y: y in x,
        "not_contains": lambda x, y: y not in x,
        "startswith": lambda x, y: x.startswith(y),
        "endswith": lambda x, y: x.endswith(y),
        
        # Component operators
        "dirname_equals": lambda x, y: os.path.dirname(x) == y,
        "basename_equals": lambda x, y: os.path.basename(x) == y,
        "extension_equals": lambda x, y: os.path.splitext(x)[1] == y,
        
        # Validation operators
        "is_valid": lambda x, y: bool(Filter.PATH_PATTERN.match(x)),
        "is_invalid": lambda x, y: not bool(Filter.PATH_PATTERN.match(x)),
        
        # Special operators
        "is_absolute": lambda x, y: os.path.isabs(x),
        "is_relative": lambda x, y: not os.path.isabs(x),
        "has_extension": lambda x, y: bool(os.path.splitext(x)[1]),
        "no_extension": lambda x, y: not bool(os.path.splitext(x)[1])
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize path filter.
        
        Args:
            config: Configuration dictionary containing:
                - field: Field to compare
                - operator: Path operator
                - value: Path or path component to compare against
                - component: Path component to compare (optional)
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
        
        # Validate path if needed
        if self.operator in ["dirname_equals", "basename_equals", "extension_equals"]:
            if not self.PATH_PATTERN.match(self.value):
                raise ValueError(f"Invalid path: {self.value}")
        
        # Get operator function
        self._operator_func = self.OPERATORS[self.operator]
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on path comparison.
        
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