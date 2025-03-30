"""
UUID filter component for PySyslog LFC
"""

import logging
import re
import uuid
from typing import Dict, Any, Callable, Union, List
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on UUID comparisons.
    
    This filter allows comparing UUID field values against specified values
    using various operators. It supports UUID validation, version checks,
    and component-based comparisons.
    
    Configuration:
        - field: Field to compare (required)
        - operator: UUID operator (required)
        - value: UUID to compare against (required)
        - version: UUID version to validate (1-5, optional)
        - invert: Whether to invert the match (default: False)
    """
    
    # UUID regex pattern
    UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
    
    # Valid operators and their functions
    OPERATORS = {
        # UUID operators
        "equals": lambda x, y: x == y,
        "not_equals": lambda x, y: x != y,
        "contains": lambda x, y: y in x,
        "not_contains": lambda x, y: y not in x,
        
        # Version operators
        "version_equals": lambda x, y: x.version == y,
        "version_not_equals": lambda x, y: x.version != y,
        
        # Validation operators
        "is_valid": lambda x, y: bool(x),
        "is_invalid": lambda x, y: not bool(x),
        
        # Special operators
        "is_nil": lambda x, y: x.int == 0,
        "is_max": lambda x, y: x.int == 0xffffffffffffffffffffffffffffffff
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize UUID filter.
        
        Args:
            config: Configuration dictionary containing:
                - field: Field to compare
                - operator: UUID operator
                - value: UUID to compare against
                - version: UUID version to validate (1-5, optional)
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
        
        # Get and validate version
        self.version = config.get("version")
        if self.version is not None:
            try:
                self.version = int(self.version)
                if not 1 <= self.version <= 5:
                    raise ValueError("Version must be between 1 and 5")
            except (ValueError, TypeError):
                raise ValueError("Version must be an integer between 1 and 5")
        
        # Get and validate value
        self.value = config.get("value")
        if self.value is None:
            raise ValueError("value parameter is required")
        self._validate_string(self.value, "value")
        
        # Validate UUID format
        if not self.UUID_PATTERN.match(self.value):
            raise ValueError(f"Invalid UUID format: {self.value}")
        
        # Parse UUID
        try:
            self.value = uuid.UUID(self.value)
            if self.version and self.value.version != self.version:
                raise ValueError(f"UUID version mismatch: expected {self.version}, got {self.value.version}")
        except ValueError as e:
            raise ValueError(f"Invalid UUID: {e}")
        
        # Get operator function
        self._operator_func = self.OPERATORS[self.operator]
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on UUID comparison.
        
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
            
            # Parse UUID
            try:
                field_value = uuid.UUID(field_value)
                if self.version and field_value.version != self.version:
                    return False
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