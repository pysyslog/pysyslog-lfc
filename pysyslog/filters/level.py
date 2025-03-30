"""
Level filter component for PySyslog LFC
"""

import logging
from typing import Dict, Any, Set
from .base import FilterComponent, FilterStage

class Filter(FilterComponent):
    """Filter messages based on log levels.
    
    This filter allows matching message fields against standard log levels
    and syslog severity levels. It supports case-insensitive matching and
    can invert the match result.
    
    Configuration:
        - field: Field to compare (required)
        - op: Level operator (required)
        - value: Level or list of levels to match (required)
        - stage: Where to apply the filter (default: parser)
        - invert: Whether to invert the match (default: false)
    """
    
    # Standard log levels with numeric values
    STANDARD_LEVELS = {
        "debug": 10,
        "info": 20,
        "warning": 30,
        "error": 40,
        "critical": 50
    }
    
    # Syslog severity levels with numeric values
    SYSLOG_LEVELS = {
        "emerg": 0,
        "alert": 1,
        "crit": 2,
        "err": 3,
        "warning": 4,
        "notice": 5,
        "info": 6,
        "debug": 7
    }
    
    # Valid operators and their functions
    OPERATORS = {
        "eq": lambda x, y: x == y,
        "ne": lambda x, y: x != y,
        "in": lambda x, y: x in y,
        "not_in": lambda x, y: x not in y,
        "ge": lambda x, y: x >= y,
        "gt": lambda x, y: x > y,
        "le": lambda x, y: x <= y,
        "lt": lambda x, y: x < y
    }
    
    # Security limits
    MAX_LEVELS = 100  # Maximum number of levels in a list
    MAX_LEVEL_LENGTH = 20  # Maximum length of a level name
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize level filter.
        
        Args:
            config: Configuration dictionary containing:
                - flow_name: Name of the flow this filter belongs to (required)
                - type: Filter type (required)
                - field: Field to compare (required)
                - op: Level operator (required)
                - value: Level or list of levels to match (required)
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
        if self.value is None:
            raise ValueError("value parameter is required")
            
        # Parse value based on operator
        if self.op in ["in", "not_in"]:
            # List of levels
            if not isinstance(self.value, list):
                raise ValueError("value must be a list for 'in' and 'not_in' operators")
            if len(self.value) > self.MAX_LEVELS:
                raise ValueError(f"Too many levels: {len(self.value)}")
            # Convert levels to lowercase and validate
            self.value = {level.lower() for level in self.value}
            valid_levels = set(self.STANDARD_LEVELS.keys()) | set(self.SYSLOG_LEVELS.keys())
            invalid_levels = self.value - valid_levels
            if invalid_levels:
                raise ValueError(f"Invalid levels: {', '.join(invalid_levels)}")
        else:
            # Single level
            if not isinstance(self.value, str):
                raise ValueError("value must be a string for single-level operators")
            if len(self.value) > self.MAX_LEVEL_LENGTH:
                raise ValueError(f"Level name too long: {len(self.value)}")
            # Convert to lowercase and validate
            self.value = self.value.lower()
            valid_levels = set(self.STANDARD_LEVELS.keys()) | set(self.SYSLOG_LEVELS.keys())
            if self.value not in valid_levels:
                raise ValueError(f"Invalid level: {self.value}")
            # Convert to numeric value
            self.value = self.STANDARD_LEVELS.get(self.value, self.SYSLOG_LEVELS[self.value])
        
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
        
        # Validate field value is a valid level
        field_value = self._test_data[self.field]
        if isinstance(field_value, str):
            field_value = field_value.lower()
            valid_levels = set(self.STANDARD_LEVELS.keys()) | set(self.SYSLOG_LEVELS.keys())
            if field_value not in valid_levels:
                raise ValueError(f"Field '{self.field}' must contain valid log levels")
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on log level.
        
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
                
            # Convert to string and lowercase
            if not isinstance(field_value, str):
                field_value = str(field_value)
            field_value = field_value.lower()
            
            # Convert to numeric value if needed
            if self.op not in ["in", "not_in"]:
                field_value = self.STANDARD_LEVELS.get(field_value, self.SYSLOG_LEVELS.get(field_value))
                if field_value is None:
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