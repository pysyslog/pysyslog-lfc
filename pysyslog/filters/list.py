"""
List filter component for PySyslog LFC
"""

import logging
from typing import Dict, Any, Callable, List, Set
from .base import FilterComponent, FilterStage

class Filter(FilterComponent):
    """Filter messages based on list operations.
    
    This filter allows performing various operations on list fields, such as
    checking for containment, emptiness, and set operations. It supports
    case-sensitive and case-insensitive string comparisons.
    
    Configuration:
        - field: Field to compare (required)
        - op: List operator (required)
        - value: Value(s) to compare against (required)
        - stage: Where to apply the filter (default: parser)
        - invert: Whether to invert the match (default: false)
        - case_sensitive: Whether string comparisons are case sensitive (default: true)
    """
    
    # Valid operators and their functions
    OPERATORS = {
        # Basic operations
        "eq": lambda x, y: x == y,
        "ne": lambda x, y: x != y,
        
        # Containment operations
        "contains": lambda x, y: y in x,
        "not_contains": lambda x, y: y not in x,
        "contains_all": lambda x, y: all(v in x for v in y),
        "contains_any": lambda x, y: any(v in x for v in y),
        
        # Size operations
        "empty": lambda x, y: len(x) == 0,
        "not_empty": lambda x, y: len(x) > 0,
        "size_eq": lambda x, y: len(x) == y,
        "size_ne": lambda x, y: len(x) != y,
        "size_gt": lambda x, y: len(x) > y,
        "size_ge": lambda x, y: len(x) >= y,
        "size_lt": lambda x, y: len(x) < y,
        "size_le": lambda x, y: len(x) <= y
    }
    
    # Security limits
    MAX_LIST_SIZE = 1000  # Maximum list size
    MAX_ITEM_LENGTH = 1000  # Maximum item length
    MAX_ITEMS = 100  # Maximum number of items in value list
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize list filter.
        
        Args:
            config: Configuration dictionary containing:
                - flow_name: Name of the flow this filter belongs to (required)
                - type: Filter type (required)
                - field: Field to compare (required)
                - op: List operator (required)
                - value: Value(s) to compare against (required)
                - stage: Where to apply the filter (default: parser)
                - invert: Whether to invert the match (default: false)
                - case_sensitive: Whether string comparisons are case sensitive (default: true)
                
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
            
        # Get optional parameters
        self.case_sensitive = bool(config.get("case_sensitive", True))
        
        # Process value based on operator
        if self.op in ["contains_all", "contains_any"]:
            # List of values
            if not isinstance(self.value, list):
                self.value = [self.value]
            if len(self.value) > self.MAX_ITEMS:
                raise ValueError(f"Too many items: {len(self.value)}")
            self._validate_list(self.value, "value")
            if not self.case_sensitive and all(isinstance(v, str) for v in self.value):
                self.value = [v.lower() for v in self.value]
        elif self.op in ["size_eq", "size_ne", "size_gt", "size_ge", "size_lt", "size_le"]:
            # Numeric value
            try:
                self.value = int(self.value)
                if self.value < 0:
                    raise ValueError("Size must be non-negative")
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid size value: {e}")
        else:
            # Single value
            if isinstance(self.value, list):
                raise ValueError("Single value expected")
            if isinstance(self.value, str) and len(self.value) > self.MAX_ITEM_LENGTH:
                raise ValueError(f"Value too long: {len(self.value)}")
            if not self.case_sensitive and isinstance(self.value, str):
                self.value = self.value.lower()
        
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
        
        # Validate field value is a list
        field_value = self._test_data[self.field]
        if not isinstance(field_value, list):
            raise ValueError(f"Field '{self.field}' must be a list")
        
        # Validate list size
        if len(field_value) > self.MAX_LIST_SIZE:
            raise ValueError(f"List too large: {len(field_value)}")
        
        # Validate item lengths
        if all(isinstance(v, str) for v in field_value):
            if any(len(v) > self.MAX_ITEM_LENGTH for v in field_value):
                raise ValueError("List contains items that are too long")
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on list operations.
        
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
            
            # Convert to list if needed
            if not isinstance(field_value, list):
                field_value = [field_value]
            
            # Validate list size
            if len(field_value) > self.MAX_LIST_SIZE:
                return False
            
            # Convert to lowercase if case-insensitive
            if not self.case_sensitive and all(isinstance(v, str) for v in field_value):
                field_value = [v.lower() for v in field_value]
            
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