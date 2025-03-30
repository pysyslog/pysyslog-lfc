"""
Timestamp filter component for PySyslog LFC
"""

import logging
from datetime import datetime
from typing import Dict, Any, Union
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on timestamp field values"""
    
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
        if not self.value:
            raise ValueError("value parameter is required")
            
        # Optional parameters
        self.invert = config.get("invert", False)
        self.format = config.get("format", "%Y-%m-%d %H:%M:%S")
        
        # Validate operator
        valid_operators = {
            "before": self._before,
            "after": self._after,
            "between": self._between,
            "equals": self._equals
        }
        
        if self.operator not in valid_operators:
            raise ValueError(f"Invalid operator: {self.operator}. Must be one of: {', '.join(valid_operators.keys())}")
            
        self._operator_func = valid_operators[self.operator]
        
        # Parse timestamp value(s)
        try:
            if self.operator == "between":
                if not isinstance(self.value, list) or len(self.value) != 2:
                    raise ValueError("Value must be a list of two timestamps for 'between' operator")
                self.value = [
                    datetime.strptime(self.value[0], self.format),
                    datetime.strptime(self.value[1], self.format)
                ]
            else:
                self.value = datetime.strptime(self.value, self.format)
        except ValueError as e:
            raise ValueError(f"Invalid timestamp format: {e}")
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on timestamp field value
        
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
                
            # Parse timestamp
            try:
                timestamp = datetime.strptime(field_value, self.format)
            except ValueError:
                return False
            
            # Apply operator
            result = self._operator_func(timestamp)
            
            # Apply invert if specified
            if self.invert:
                result = not result
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error filtering message: {e}", exc_info=True)
            return False
    
    def _before(self, timestamp: datetime) -> bool:
        """Before specified timestamp"""
        return timestamp < self.value
    
    def _after(self, timestamp: datetime) -> bool:
        """After specified timestamp"""
        return timestamp > self.value
    
    def _between(self, timestamp: datetime) -> bool:
        """Between two timestamps (inclusive)"""
        return self.value[0] <= timestamp <= self.value[1]
    
    def _equals(self, timestamp: datetime) -> bool:
        """Equals specified timestamp"""
        return timestamp == self.value
    
    def close(self) -> None:
        """Cleanup resources"""
        pass 