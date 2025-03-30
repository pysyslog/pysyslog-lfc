"""
Regex filter component for PySyslog LFC
"""

import logging
import re
from typing import Dict, Any
from .base import FilterComponent, FilterStage

class Filter(FilterComponent):
    """Filter messages based on regex pattern matching.
    
    This filter allows matching message fields against regular expressions.
    It supports case-sensitive and case-insensitive matching, and can invert
    the match result.
    
    Configuration:
        - field: Field to compare (required)
        - op: Regex operator (required)
        - value: Regex pattern to match (required)
        - stage: Where to apply the filter (default: parser)
        - invert: Whether to invert the match (default: false)
        - case_sensitive: Whether matching is case sensitive (default: true)
    """
    
    # Valid operators and their functions
    OPERATORS = {
        "match": lambda x, y: bool(y.search(x)),
        "not_match": lambda x, y: not bool(y.search(x)),
        "contains": lambda x, y: bool(y.search(x)),
        "not_contains": lambda x, y: not bool(y.search(x)),
        "starts_with": lambda x, y: bool(y.match(x)),
        "not_starts_with": lambda x, y: not bool(y.match(x)),
        "ends_with": lambda x, y: bool(y.search(x + "$")),
        "not_ends_with": lambda x, y: not bool(y.search(x + "$"))
    }
    
    # Security limits
    MAX_PATTERN_LENGTH = 1000  # Maximum pattern length
    MAX_MATCH_LENGTH = 10000  # Maximum match length
    MAX_CAPTURE_GROUPS = 10  # Maximum number of capture groups
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize regex filter.
        
        Args:
            config: Configuration dictionary containing:
                - flow_name: Name of the flow this filter belongs to (required)
                - type: Filter type (required)
                - field: Field to compare (required)
                - op: Regex operator (required)
                - value: Regex pattern to match (required)
                - stage: Where to apply the filter (default: parser)
                - invert: Whether to invert the match (default: false)
                - case_sensitive: Whether matching is case sensitive (default: true)
                
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
        
        # Get and validate value (pattern)
        self.value = config.get("value")
        if not self.value:
            raise ValueError("value parameter is required")
        self._validate_string(self.value, "value")
        
        # Validate pattern length
        if len(self.value) > self.MAX_PATTERN_LENGTH:
            raise ValueError(f"Pattern too long: {len(self.value)}")
        
        # Get optional parameters
        self.case_sensitive = bool(config.get("case_sensitive", True))
        
        # Compile pattern with flags
        flags = 0 if self.case_sensitive else re.IGNORECASE
        try:
            self.value = self._compile_pattern(self.value, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
    
    def _validate_config(self) -> None:
        """Validate filter-specific configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate field exists in data
        if self.field not in self._test_data:
            raise ValueError(f"Field '{self.field}' not found in test data")
        
        # Validate field value can be matched
        field_value = self._test_data[self.field]
        if isinstance(field_value, str):
            if len(field_value) > self.MAX_MATCH_LENGTH:
                raise ValueError(f"Field value too long: {len(field_value)}")
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on regex pattern matching.
        
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
            
            # Validate length
            if len(field_value) > self.MAX_MATCH_LENGTH:
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