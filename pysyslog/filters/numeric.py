"""
Numeric filter component for PySyslog LFC
"""

import logging
from typing import Dict, Any, Callable
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on numeric comparisons.
    
    This filter allows comparing numeric field values against specified values
    using various operators. It supports integer and floating-point comparisons
    with proper type conversion and validation.
    
    Configuration:
        - field: Field to compare (required)
        - operator: Comparison operator (required)
        - value: Numeric value to compare against (required)
        - invert: Whether to invert the match (default: False)
    """
    
    # Valid operators and their functions
    OPERATORS = {
        "eq": lambda x, y: x == y,
        "ne": lambda x, y: x != y,
        "gt": lambda x, y: x > y,
        "ge": lambda x, y: x >= y,
        "lt": lambda x, y: x < y,
        "le": lambda x, y: x <= y
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize numeric filter.
        
        Args:
            config: Configuration dictionary containing:
                - field: Field to compare
                - operator: Comparison operator
                - value: Numeric value to compare against
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
        self.value = self._convert_to_float(self.value)
        
        # Get operator function
        self._operator_func = self.OPERATORS[self.operator]
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on numeric comparison.
        
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
            
            # Convert to float
            try:
                field_value = self._convert_to_float(field_value)
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