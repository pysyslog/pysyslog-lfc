"""
List filter component for PySyslog LFC
"""

import logging
from typing import Dict, Any, Callable, List, Set
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on list operations.
    
    This filter allows performing various operations on list fields, such as
    checking for containment, emptiness, and set operations. It supports
    case-sensitive and case-insensitive string comparisons.
    
    Configuration:
        - field: Field to compare (required)
        - operator: List operator (required)
        - value: Value(s) to compare against (required)
        - case_sensitive: Whether string comparisons are case sensitive (default: True)
        - invert: Whether to invert the match (default: False)
    """
    
    # Valid operators and their functions
    OPERATORS = {
        "contains": lambda x, y: y in x,
        "not_contains": lambda x, y: y not in x,
        "contains_all": lambda x, y: all(v in x for v in y),
        "contains_any": lambda x, y: any(v in x for v in y),
        "empty": lambda x, y: len(x) == 0,
        "not_empty": lambda x, y: len(x) > 0
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize list filter.
        
        Args:
            config: Configuration dictionary containing:
                - field: Field to compare
                - operator: List operator
                - value: Value(s) to compare against
                - case_sensitive: Whether string comparisons are case sensitive (default: True)
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
            
        # Get optional parameters
        self.case_sensitive = bool(config.get("case_sensitive", True))
        
        # Convert value to list if needed
        if self.operator in ["contains_all", "contains_any"]:
            if not isinstance(self.value, list):
                self.value = [self.value]
            self._validate_list(self.value, "value")
            if not self.case_sensitive and all(isinstance(v, str) for v in self.value):
                self.value = [v.lower() for v in self.value]
        
        # Get operator function
        self._operator_func = self.OPERATORS[self.operator]
    
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