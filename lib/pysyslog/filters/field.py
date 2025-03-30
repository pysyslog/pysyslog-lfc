"""
Field filter component for PySyslog LFC
"""

import re
from typing import Dict, Any, Optional, Union
from ..components import FilterComponent

class Filter(FilterComponent):
    """Field filter component"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.field = config.get("field")
        self.operator = config.get("operator")
        self.value = config.get("value")
        self.invert = config.get("invert", False)
        
        if not self.field:
            raise ValueError("Field is required for field filter")
        if not self.operator:
            raise ValueError("Operator is required for field filter")
        if self.value is None:
            raise ValueError("Value is required for field filter")
        
        # Validate operator
        valid_operators = {
            # Numeric operators
            "eq": self._eq,
            "ne": self._ne,
            "gt": self._gt,
            "ge": self._ge,
            "lt": self._lt,
            "le": self._le,
            # String operators
            "contains": self._contains,
            "startswith": self._startswith,
            "endswith": self._endswith,
            "matches": self._matches
        }
        
        if self.operator not in valid_operators:
            raise ValueError(f"Unknown operator: {self.operator}")
        
        self.operator_func = valid_operators[self.operator]
        
        # Compile regex if using matches operator
        if self.operator == "matches":
            try:
                self.regex = re.compile(str(self.value))
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}")
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on field value
        
        Args:
            data: Parsed message data
            
        Returns:
            bool: True if field matches condition (or doesn't match if inverted)
        """
        try:
            # Get field value
            field_value = data.get(self.field)
            if field_value is None:
                return False
            
            # Apply operator
            matches = self.operator_func(field_value, self.value)
            
            # Return based on invert setting
            return not matches if self.invert else matches
            
        except Exception as e:
            self.logger.error(f"Error filtering message: {e}")
            return False
    
    def _eq(self, a: Any, b: Any) -> bool:
        """Equal to operator"""
        return a == b
    
    def _ne(self, a: Any, b: Any) -> bool:
        """Not equal to operator"""
        return a != b
    
    def _gt(self, a: Any, b: Any) -> bool:
        """Greater than operator"""
        try:
            return float(a) > float(b)
        except (ValueError, TypeError):
            return False
    
    def _ge(self, a: Any, b: Any) -> bool:
        """Greater than or equal operator"""
        try:
            return float(a) >= float(b)
        except (ValueError, TypeError):
            return False
    
    def _lt(self, a: Any, b: Any) -> bool:
        """Less than operator"""
        try:
            return float(a) < float(b)
        except (ValueError, TypeError):
            return False
    
    def _le(self, a: Any, b: Any) -> bool:
        """Less than or equal operator"""
        try:
            return float(a) <= float(b)
        except (ValueError, TypeError):
            return False
    
    def _contains(self, a: str, b: str) -> bool:
        """Contains substring operator"""
        return str(b) in str(a)
    
    def _startswith(self, a: str, b: str) -> bool:
        """Starts with operator"""
        return str(a).startswith(str(b))
    
    def _endswith(self, a: str, b: str) -> bool:
        """Ends with operator"""
        return str(a).endswith(str(b))
    
    def _matches(self, a: str, b: str) -> bool:
        """Matches regex operator"""
        return bool(self.regex.search(str(a)))
    
    def close(self) -> None:
        """Cleanup resources"""
        pass 