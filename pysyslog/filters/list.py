"""
List filter component for PySyslog LFC
"""

import logging
from typing import Dict, Any, List, Union
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on list field values"""
    
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
        self.case_sensitive = config.get("case_sensitive", True)
        
        # Validate operator
        valid_operators = {
            "contains": self._contains,
            "not_contains": self._not_contains,
            "contains_all": self._contains_all,
            "contains_any": self._contains_any,
            "empty": self._empty,
            "not_empty": self._not_empty
        }
        
        if self.operator not in valid_operators:
            raise ValueError(f"Invalid operator: {self.operator}. Must be one of: {', '.join(valid_operators.keys())}")
            
        self._operator_func = valid_operators[self.operator]
        
        # Convert value to list if needed
        if self.operator in ["contains_all", "contains_any"]:
            if not isinstance(self.value, list):
                self.value = [self.value]
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on list field value
        
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
                
            # Ensure field value is a list
            if not isinstance(field_value, list):
                field_value = [field_value]
            
            # Apply operator
            result = self._operator_func(field_value)
            
            # Apply invert if specified
            if self.invert:
                result = not result
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error filtering message: {e}", exc_info=True)
            return False
    
    def _contains(self, field_value: List[Any]) -> bool:
        """List contains value"""
        if not self.case_sensitive and isinstance(self.value, str):
            return any(str(v).lower() == self.value.lower() for v in field_value)
        return self.value in field_value
    
    def _not_contains(self, field_value: List[Any]) -> bool:
        """List does not contain value"""
        return not self._contains(field_value)
    
    def _contains_all(self, field_value: List[Any]) -> bool:
        """List contains all values"""
        if not self.case_sensitive and all(isinstance(v, str) for v in self.value):
            return all(any(str(fv).lower() == str(v).lower() for fv in field_value) for v in self.value)
        return all(v in field_value for v in self.value)
    
    def _contains_any(self, field_value: List[Any]) -> bool:
        """List contains any value"""
        if not self.case_sensitive and all(isinstance(v, str) for v in self.value):
            return any(any(str(fv).lower() == str(v).lower() for fv in field_value) for v in self.value)
        return any(v in field_value for v in self.value)
    
    def _empty(self, field_value: List[Any]) -> bool:
        """List is empty"""
        return len(field_value) == 0
    
    def _not_empty(self, field_value: List[Any]) -> bool:
        """List is not empty"""
        return len(field_value) > 0
    
    def close(self) -> None:
        """Cleanup resources"""
        pass 