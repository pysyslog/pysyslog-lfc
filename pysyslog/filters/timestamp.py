"""
Timestamp filter component for PySyslog LFC
"""

import logging
from datetime import datetime
from typing import Dict, Any, Callable, List, Tuple
from .base import FilterComponent, FilterStage

class Filter(FilterComponent):
    """Filter messages based on timestamp comparisons.
    
    This filter allows comparing timestamp field values against specified values
    using various operators. It supports date and time comparisons with proper
    format validation and conversion.
    
    Configuration:
        - field: Field to compare (required)
        - op: Comparison operator (required)
        - value: Timestamp value(s) to compare against (required)
        - format: Timestamp format string (default: "%Y-%m-%d %H:%M:%S")
        - stage: Where to apply the filter (default: parser)
        - invert: Whether to invert the match (default: false)
    """
    
    # Valid operators and their functions
    OPERATORS = {
        "lt": lambda x, y: x < y,
        "gt": lambda x, y: x > y,
        "between": lambda x, y: y[0] <= x <= y[1],
        "eq": lambda x, y: x == y,
        "ne": lambda x, y: x != y,
        "le": lambda x, y: x <= y,
        "ge": lambda x, y: x >= y
    }
    
    # Security limits
    MAX_TIMESTAMP_LENGTH = 100  # Maximum timestamp string length
    MAX_FORMAT_LENGTH = 100  # Maximum format string length
    MAX_RANGE_DAYS = 365  # Maximum date range in days
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize timestamp filter.
        
        Args:
            config: Configuration dictionary containing:
                - flow_name: Name of the flow this filter belongs to (required)
                - type: Filter type (required)
                - field: Field to compare (required)
                - op: Comparison operator (required)
                - value: Timestamp value(s) to compare against (required)
                - format: Timestamp format string (default: "%Y-%m-%d %H:%M:%S")
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
        
        # Get and validate format
        self.format = config.get("format", "%Y-%m-%d %H:%M:%S")
        self._validate_string(self.format, "format")
        if len(self.format) > self.MAX_FORMAT_LENGTH:
            raise ValueError(f"Format string too long: {len(self.format)}")
        
        # Get and validate value
        self.value = config.get("value")
        if not self.value:
            raise ValueError("value parameter is required")
            
        # Parse value based on operator
        if self.op == "between":
            if not isinstance(self.value, list) or len(self.value) != 2:
                raise ValueError("Value must be a list of two timestamps for 'between' operator")
            self._validate_list(self.value, "value")
            self.value = [
                self._convert_to_datetime(self.value[0], self.format),
                self._convert_to_datetime(self.value[1], self.format)
            ]
            if self.value[0] > self.value[1]:
                raise ValueError("Invalid date range: start date must be before end date")
            # Check date range limit
            days = (self.value[1] - self.value[0]).days
            if days > self.MAX_RANGE_DAYS:
                raise ValueError(f"Date range too large: {days} days")
        else:
            self.value = self._convert_to_datetime(self.value, self.format)
        
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
        
        # Validate field value can be converted to datetime
        field_value = self._test_data[self.field]
        if isinstance(field_value, str):
            if len(field_value) > self.MAX_TIMESTAMP_LENGTH:
                raise ValueError(f"Timestamp too long: {len(field_value)}")
            try:
                self._convert_to_datetime(field_value, self.format)
            except ValueError:
                raise ValueError(f"Field '{self.field}' must contain valid timestamps")
    
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