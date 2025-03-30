"""
Numeric filter component for PySyslog LFC
"""

import logging
from typing import Dict, Any, Callable
from .base import FilterComponent, FilterStage

class Filter(FilterComponent):
    """Filter messages based on numeric comparisons.
    
    This filter allows comparing numeric field values against specified values
    using various operators. It supports integer and floating-point comparisons
    with proper type conversion and validation.
    
    Configuration:
        - field: Field to compare (required)
        - op: Comparison operator (required)
        - value: Numeric value to compare against (required for single-value operations)
        - min: Lower bound for range operations (optional)
        - max: Upper bound for range operations (optional)
        - stage: Where to apply the filter (default: parser)
        - invert: Whether to invert the match (default: false)
    """
    
    # Valid operators and their functions
    OPERATORS = {
        # Single value operations
        "eq": lambda x, y: x == y,
        "ne": lambda x, y: x != y,
        "gt": lambda x, y: x > y,
        "ge": lambda x, y: x >= y,
        "lt": lambda x, y: x < y,
        "le": lambda x, y: x <= y,
        # Range operations
        "between": lambda x, y: y[0] <= x <= y[1],
        "outside": lambda x, y: x < y[0] or x > y[1]
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize numeric filter.
        
        Args:
            config: Configuration dictionary containing:
                - flow_name: Name of the flow this filter belongs to (required)
                - type: Filter type (required)
                - field: Field to compare (required)
                - op: Comparison operator (required)
                - value: Numeric value to compare against (required for single-value operations)
                - min: Lower bound for range operations (optional)
                - max: Upper bound for range operations (optional)
                - stage: Where to apply the filter (default: parser)
                - invert: Whether to invert the match (default: false)
                
        Raises:
            ValueError: If configuration is invalid
        """
        super().__init__(config)
        
        # Get and validate operator
        self.op = config.get("op")
        if not self.op:
            raise ValueError("op parameter is required")
        if self.op not in self.OPERATORS:
            raise ValueError(f"Invalid operator: {self.op}. Must be one of: {', '.join(self.OPERATORS.keys())}")
        
        # Get and validate value based on operation type
        if self.op in ["between", "outside"]:
            # Range operation
            self.min_value = config.get("min")
            self.max_value = config.get("max")
            if self.min_value is None or self.max_value is None:
                raise ValueError("min and max parameters are required for range operations")
            self.min_value = self._convert_to_float(self.min_value)
            self.max_value = self._convert_to_float(self.max_value)
            if self.min_value > self.max_value:
                raise ValueError("min value must be less than or equal to max value")
            self.value = (self.min_value, self.max_value)
        else:
            # Single value operation
            self.value = config.get("value")
            if self.value is None:
                raise ValueError("value parameter is required for single-value operations")
            self.value = self._convert_to_float(self.value)
        
        # Get operator function
        self._operator_func = self.OPERATORS[self.op]
    
    def _validate_config(self) -> None:
        """Validate filter-specific configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate field exists in data
        if self.field not in self._test_data:
            raise ValueError(f"Field '{self.field}' not found in test data")
        
        # Validate field value can be converted to float
        try:
            self._convert_to_float(self._test_data[self.field])
        except ValueError:
            raise ValueError(f"Field '{self.field}' must contain numeric values")
    
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