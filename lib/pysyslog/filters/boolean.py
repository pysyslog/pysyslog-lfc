"""
Boolean filter component for PySyslog LFC
"""

import logging
from typing import Dict, Any, Union
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on boolean field values"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Required parameters
        self.field = config.get("field")
        if not self.field:
            raise ValueError("field parameter is required")
            
        self.operator = config.get("operator")
        if not self.operator:
            raise ValueError("operator parameter is required")
            
        self.value = config.get("value")
        if self.value is None:
            raise ValueError("value parameter is required")
            
        # Optional parameters
        self.invert = config.get("invert", False)
        
        # Validate operator
        valid_operators = {
            "equals": self._equals,
            "not_equals": self._not_equals,
            "is_true": self._is_true,
            "is_false": self._is_false
        }
        
        if self.operator not in valid_operators:
            raise ValueError(f"Invalid operator: {self.operator}. Must be one of: {', '.join(valid_operators.keys())}")
            
        self._operator_func = valid_operators[self.operator]
        
        # Convert value to boolean
        if self.operator in ["equals", "not_equals"]:
            if isinstance(self.value, str):
                self.value = self.value.lower() in ["true", "1", "yes", "on"]
            else:
                self.value = bool(self.value)
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on boolean field value
        
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
                
            # Convert field value to boolean
            if isinstance(field_value, str):
                field_value = field_value.lower() in ["true", "1", "yes", "on"]
            else:
                field_value = bool(field_value)
            
            # Apply operator
            result = self._operator_func(field_value)
            
            # Apply invert if specified
            if self.invert:
                result = not result
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error filtering message: {e}", exc_info=True)
            return False
    
    def _equals(self, field_value: bool) -> bool:
        """Field value equals specified value"""
        return field_value == self.value
    
    def _not_equals(self, field_value: bool) -> bool:
        """Field value does not equal specified value"""
        return field_value != self.value
    
    def _is_true(self, field_value: bool) -> bool:
        """Field value is true"""
        return field_value is True
    
    def _is_false(self, field_value: bool) -> bool:
        """Field value is false"""
        return field_value is False
    
    def close(self) -> None:
        """Cleanup resources"""
        pass 