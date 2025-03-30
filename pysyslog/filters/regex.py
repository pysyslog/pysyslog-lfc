"""
Regex filter component for PySyslog LFC
"""

import re
from typing import Dict, Any, Optional
from ..components import FilterComponent

class Filter(FilterComponent):
    """Regex filter component"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.pattern = config.get("pattern")
        self.field = config.get("field", "message")
        self.invert = config.get("invert", False)
        self.case_sensitive = config.get("case_sensitive", True)
        
        if not self.pattern:
            raise ValueError("Pattern is required for regex filter")
        
        # Compile regex pattern
        flags = 0 if self.case_sensitive else re.IGNORECASE
        try:
            self.regex = re.compile(self.pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages using regex pattern
        
        Args:
            data: Parsed message data
            
        Returns:
            bool: True if message matches pattern (or doesn't match if inverted)
        """
        try:
            # Get field value
            value = data.get(self.field, "")
            if not isinstance(value, str):
                value = str(value)
            
            # Check pattern match
            matches = bool(self.regex.search(value))
            
            # Return based on invert setting
            return not matches if self.invert else matches
            
        except Exception as e:
            self.logger.error(f"Error filtering message: {e}")
            return False
    
    def close(self) -> None:
        """Cleanup resources"""
        pass 