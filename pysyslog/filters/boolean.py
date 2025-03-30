"""
Boolean filter component for PySyslog LFC
"""

import logging
from typing import Dict, Any, Callable
from .base import FilterComponent, FilterStage

class Filter(FilterComponent):
    """Filter messages based on boolean operations.
    
    This filter allows comparing boolean field values against specified values
    using various operators. It supports string, numeric, and boolean value
    conversion with proper validation.
    
    Configuration:
        - field: Field to compare (required)
        - op: Boolean operator (required)
        - value: Boolean value to compare against (required)
        - stage: Where to apply the filter (default: parser)
        - invert: Whether to invert the match (default: false)
    """
    
    # Valid operators and their functions
    OPERATORS = {
        "eq": lambda x, y: x == y,
        "ne": lambda x, y: x != y,
        "is_true": lambda x, y: x is True,
        "is_false": lambda x, y: x is False,
        "is_null": lambda x, y: x is None,
        "is_not_null": lambda x, y: x is not None
    }
    
    # Security limits
    MAX_STRING_LENGTH = 100  # Maximum string length for boolean conversion
    MAX_NUMERIC_VALUE = 1e308  # Maximum numeric value for boolean conversion
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize boolean filter.
        
        Args:
            config: Configuration dictionary containing:
                - flow_name: Name of the flow this filter belongs to (required)
                - type: Filter type (required)
                - field: Field to compare (required)
                - op: Boolean operator (required)
                - value: Boolean value to compare against (required)
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
        
        # Get and validate value
        self.value = config.get("value")
        if self.value is None and self.op not in ["is_null", "is_not_null"]:
            raise ValueError("value parameter is required")
            
        # Convert value based on operator
        if self.op not in ["is_null", "is_not_null"]:
            try:
                self.value = self._convert_to_bool(self.value)
            except ValueError as e:
                raise ValueError(f"Invalid boolean value: {e}")
        
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
        
        # Validate field value can be converted to boolean
        field_value = self._test_data[self.field]
        if self.op not in ["is_null", "is_not_null"]:
            try:
                self._convert_to_bool(field_value)
            except ValueError:
                raise ValueError(f"Field '{self.field}' must contain valid boolean values")
    
    def _convert_to_bool(self, value: Any) -> bool:
        """Convert value to boolean with security limits.
        
        Args:
            value: Value to convert
            
        Returns:
            bool: Converted boolean value
            
        Raises:
            ValueError: If value cannot be converted
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            if abs(value) > self.MAX_NUMERIC_VALUE:
                raise ValueError("Numeric value too large")
            return bool(value)
        if isinstance(value, str):
            if len(value) > self.MAX_STRING_LENGTH:
                raise ValueError("String value too long")
            value = value.lower()
            if value in ("true", "1", "yes", "on"):
                return True
            if value in ("false", "0", "no", "off"):
                return False
            raise ValueError(f"Invalid boolean string: {value}")
        raise ValueError(f"Cannot convert {type(value)} to boolean")
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on boolean comparison.
        
        Args:
            data: Parsed message data
            
        Returns:
            bool: True if message should be kept, False if filtered out
        """
        try:
            # Get field value
            field_value = data.get(self.field)
            
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