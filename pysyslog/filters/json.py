"""
JSON filter component for PySyslog LFC
"""

import logging
import json
from typing import Dict, Any, Callable, Union, List
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on JSON data comparisons.
    
    This filter allows comparing JSON field values against specified values
    using various operators. It supports path-based access to nested JSON
    structures and type-specific comparisons.
    
    Configuration:
        - field: Field to compare (required)
        - operator: JSON operator (required)
        - value: Value to compare against (required)
        - path: JSON path to access nested values (optional)
        - invert: Whether to invert the match (default: False)
    """
    
    # Valid operators and their functions
    OPERATORS = {
        # Value operators
        "equals": lambda x, y: x == y,
        "not_equals": lambda x, y: x != y,
        "contains": lambda x, y: y in x if isinstance(x, (list, str)) else False,
        "not_contains": lambda x, y: y not in x if isinstance(x, (list, str)) else False,
        
        # Type operators
        "is_null": lambda x, y: x is None,
        "is_not_null": lambda x, y: x is not None,
        "is_array": lambda x, y: isinstance(x, list),
        "is_object": lambda x, y: isinstance(x, dict),
        "is_string": lambda x, y: isinstance(x, str),
        "is_number": lambda x, y: isinstance(x, (int, float)),
        "is_boolean": lambda x, y: isinstance(x, bool),
        
        # Array operators
        "array_contains": lambda x, y: y in x if isinstance(x, list) else False,
        "array_not_contains": lambda x, y: y not in x if isinstance(x, list) else False,
        "array_length": lambda x, y: len(x) == y if isinstance(x, list) else False,
        "array_empty": lambda x, y: len(x) == 0 if isinstance(x, list) else False,
        "array_not_empty": lambda x, y: len(x) > 0 if isinstance(x, list) else False
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize JSON filter.
        
        Args:
            config: Configuration dictionary containing:
                - field: Field to compare
                - operator: JSON operator
                - value: Value to compare against
                - path: JSON path to access nested values (optional)
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
        
        # Get and validate path
        self.path = config.get("path")
        if self.path:
            self._validate_string(self.path, "path")
        
        # Get and validate value
        self.value = config.get("value")
        if self.value is None and self.operator not in ["is_null", "is_not_null"]:
            raise ValueError("value parameter is required")
            
        # Parse value if it's a JSON string
        if isinstance(self.value, str):
            try:
                self.value = json.loads(self.value)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON value: {e}")
        
        # Get operator function
        self._operator_func = self.OPERATORS[self.operator]
    
    def _get_value_at_path(self, data: Any, path: str) -> Any:
        """Get value at specified JSON path.
        
        Args:
            data: JSON data to traverse
            path: Path to the desired value
            
        Returns:
            Value at the specified path
            
        Raises:
            ValueError: If path is invalid
        """
        try:
            current = data
            for key in path.split("."):
                if isinstance(current, dict):
                    current = current[key]
                elif isinstance(current, list):
                    current = current[int(key)]
                else:
                    return None
            return current
        except (KeyError, IndexError, ValueError):
            return None
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on JSON comparison.
        
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
            
            # Parse JSON if string
            if isinstance(field_value, str):
                try:
                    field_value = json.loads(field_value)
                except json.JSONDecodeError:
                    return False
            
            # Get value at path if specified
            if self.path:
                field_value = self._get_value_at_path(field_value, self.path)
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