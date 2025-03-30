"""
Regex filter component for PySyslog LFC
"""

import logging
import re
from typing import Dict, Any
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on regex pattern matching.
    
    This filter allows matching message fields against regular expressions.
    It supports case-sensitive and case-insensitive matching, and can invert
    the match result.
    
    Configuration:
        - pattern: Regex pattern to match (required)
        - field: Field to match against (required)
        - invert: Whether to invert the match (default: False)
        - case_sensitive: Whether matching is case sensitive (default: True)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize regex filter.
        
        Args:
            config: Configuration dictionary containing:
                - pattern: Regex pattern to match
                - field: Field to match against
                - invert: Whether to invert the match (default: False)
                - case_sensitive: Whether matching is case sensitive (default: True)
                
        Raises:
            ValueError: If configuration is invalid
        """
        super().__init__(config)
        
        # Get and validate pattern
        pattern = config.get("pattern")
        if not pattern:
            raise ValueError("pattern parameter is required")
        self._validate_string(pattern, "pattern")
        
        # Get and validate field
        self.field = config.get("field")
        if not self.field:
            raise ValueError("field parameter is required")
        self._validate_string(self.field, "field")
        
        # Get optional parameters
        self.case_sensitive = bool(config.get("case_sensitive", True))
        
        # Compile pattern with flags
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self.pattern = self._compile_pattern(pattern)
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on regex pattern matching.
        
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
            
            # Apply pattern matching
            result = bool(self.pattern.search(field_value))
            
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