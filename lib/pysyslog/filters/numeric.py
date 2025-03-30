"""
Numeric filter component for PySyslog LFC
"""

import logging
from typing import Dict, Any, Union
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on numeric field values"""
    
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
            "eq": self._eq,
            "ne": self._ne,
            "gt": self._gt,
            "ge": self._ge,
            "lt": self._lt,
            "le": self._le
        }
        
        if self.operator not in valid_operators:
            raise ValueError(f"Invalid operator: {self.operator}. Must be one of: {', '.join(valid_operators.keys())}")
            
        self._operator_func = valid_operators[self.operator]
        
        # Convert value to float for numeric comparison
        try:
            self.value = float(self.value)
        except (ValueError, TypeError):
            raise ValueError(f"Value must be numeric: {self.value}")
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on numeric field value
        
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
                
            # Convert to float for comparison
            try:
                field_value = float(field_value)
            except (ValueError, TypeError):
                return False
            
            # Apply operator
            result = self._operator_func(field_value)
            
            # Apply invert if specified
            if self.invert:
                result = not result
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error filtering message: {e}", exc_info=True)
            return False
    
    def _eq(self, value: float) -> bool:
        """Equal to"""
        return value == self.value
    
    def _ne(self, value: float) -> bool:
        """Not equal to"""
        return value != self.value
    
    def _gt(self, value: float) -> bool:
        """Greater than"""
        return value > self.value
    
    def _ge(self, value: float) -> bool:
        """Greater than or equal to"""
        return value >= self.value
    
    def _lt(self, value: float) -> bool:
        """Less than"""
        return value < self.value
    
    def _le(self, value: float) -> bool:
        """Less than or equal to"""
        return value <= self.value
    
    def close(self) -> None:
        """Cleanup resources"""
        pass 