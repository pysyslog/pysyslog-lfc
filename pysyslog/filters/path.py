"""
Path filter component for PySyslog LFC
"""

import logging
import os
import re
from typing import Dict, Any, Callable, Union, List
from .base import FilterComponent, FilterStage

class Filter(FilterComponent):
    """Filter messages based on file path comparisons.
    
    This filter allows comparing file path field values against specified values
    using various operators. It supports path validation, component checks,
    and file system operations.
    
    Configuration:
        - field: Field to compare (required)
        - op: Path operator (required)
        - value: Path or path component to compare against (required)
        - component: Path component to compare (optional)
        - stage: Where to apply the filter (default: parser)
        - invert: Whether to invert the match (default: false)
    """
    
    # Path regex pattern
    PATH_PATTERN = re.compile(r'^[a-zA-Z0-9\-_\./\\]+$')
    
    # Valid operators and their functions
    OPERATORS = {
        # Path operators
        "eq": lambda x, y: x == y,
        "ne": lambda x, y: x != y,
        "contains": lambda x, y: y in x,
        "not_contains": lambda x, y: y not in x,
        "starts_with": lambda x, y: x.startswith(y),
        "ends_with": lambda x, y: x.endswith(y),
        
        # Component operators
        "dirname_eq": lambda x, y: os.path.dirname(x) == y,
        "basename_eq": lambda x, y: os.path.basename(x) == y,
        "extension_eq": lambda x, y: os.path.splitext(x)[1] == y,
        
        # Validation operators
        "is_valid": lambda x, y: bool(Filter.PATH_PATTERN.match(x)),
        "is_invalid": lambda x, y: not bool(Filter.PATH_PATTERN.match(x)),
        
        # Special operators
        "is_absolute": lambda x, y: os.path.isabs(x),
        "is_relative": lambda x, y: not os.path.isabs(x),
        "has_extension": lambda x, y: bool(os.path.splitext(x)[1]),
        "no_extension": lambda x, y: not bool(os.path.splitext(x)[1])
    }
    
    # Security limits
    MAX_PATH_LENGTH = 4096  # Maximum path length (common OS limit)
    MAX_COMPONENT_LENGTH = 255  # Maximum component length (common OS limit)
    MAX_DEPTH = 100  # Maximum path depth
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize path filter.
        
        Args:
            config: Configuration dictionary containing:
                - flow_name: Name of the flow this filter belongs to (required)
                - type: Filter type (required)
                - field: Field to compare (required)
                - op: Path operator (required)
                - value: Path or path component to compare against (required)
                - component: Path component to compare (optional)
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
        self._validate_string(self.value, "value")
        
        # Validate value length
        if len(self.value) > self.MAX_PATH_LENGTH:
            raise ValueError(f"Path too long: {len(self.value)}")
        
        # Validate path if needed
        if self.op in ["dirname_eq", "basename_eq", "extension_eq"]:
            if not self.PATH_PATTERN.match(self.value):
                raise ValueError(f"Invalid path: {self.value}")
            # Validate component lengths
            components = self.value.split(os.sep)
            if len(components) > self.MAX_DEPTH:
                raise ValueError("Path too deep")
            for component in components:
                if len(component) > self.MAX_COMPONENT_LENGTH:
                    raise ValueError(f"Component too long: {len(component)}")
        
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
        
        # Validate field value can be parsed as path
        field_value = self._test_data[self.field]
        if isinstance(field_value, str):
            if len(field_value) > self.MAX_PATH_LENGTH:
                raise ValueError(f"Path too long: {len(field_value)}")
            if not self.PATH_PATTERN.match(field_value):
                raise ValueError(f"Field '{self.field}' must contain valid paths")
            # Validate component lengths
            components = field_value.split(os.sep)
            if len(components) > self.MAX_DEPTH:
                raise ValueError("Path too deep")
            for component in components:
                if len(component) > self.MAX_COMPONENT_LENGTH:
                    raise ValueError(f"Component too long: {len(component)}")
    
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
            
            # Validate length
            if len(field_value) > self.MAX_PATH_LENGTH:
                return False
            
            # Validate path format
            if not self.PATH_PATTERN.match(field_value):
                return False
            
            # Validate component lengths
            components = field_value.split(os.sep)
            if len(components) > self.MAX_DEPTH:
                return False
            for component in components:
                if len(component) > self.MAX_COMPONENT_LENGTH:
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