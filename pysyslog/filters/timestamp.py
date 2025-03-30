"""
Timestamp filter component for PySyslog LFC
"""

import logging
from datetime import datetime
from typing import Dict, Any, Callable, List, Tuple
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on timestamp comparisons.
    
    This filter allows comparing timestamp field values against specified values
    using various operators. It supports date and time comparisons with proper
    format validation and conversion.
    
    Configuration:
        - field: Field to compare (required)
        - operator: Comparison operator (required)
        - value: Timestamp value(s) to compare against (required)
        - format: Timestamp format string (default: "%Y-%m-%d %H:%M:%S")
        - invert: Whether to invert the match (default: False)
    """
    
    # Valid operators and their functions
    OPERATORS = {
        "before": lambda x, y: x < y,
        "after": lambda x, y: x > y,
        "between": lambda x, y: y[0] <= x <= y[1],
        "equals": lambda x, y: x == y
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize timestamp filter.
        
        Args:
            config: Configuration dictionary containing:
                - field: Field to compare
                - operator: Comparison operator
                - value: Timestamp value(s) to compare against
                - format: Timestamp format string (default: "%Y-%m-%d %H:%M:%S")
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
        self.format = config.get("format", "%Y-%m-%d %H:%M:%S")
        self._validate_string(self.format, "format")
        
        # Get and validate value
        self.value = config.get("value")
        if not self.value:
            raise ValueError("value parameter is required")
            
        # Parse value based on operator
        if self.operator == "between":
            if not isinstance(self.value, list) or len(self.value) != 2:
                raise ValueError("Value must be a list of two timestamps for 'between' operator")
            self._validate_list(self.value, "value")
            self.value = [
                self._convert_to_datetime(self.value[0], self.format),
                self._convert_to_datetime(self.value[1], self.format)
            ]
            if self.value[0] > self.value[1]:
                raise ValueError("Invalid date range: start date must be before end date")
        else:
            self.value = self._convert_to_datetime(self.value, self.format)
        
        # Get operator function
        self._operator_func = self.OPERATORS[self.operator]
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on timestamp comparison.
        
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
            
            # Convert to datetime
            try:
                field_value = self._convert_to_datetime(field_value, self.format)
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