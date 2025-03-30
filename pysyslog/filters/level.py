"""
Level filter component for PySyslog LFC
"""

import logging
from typing import Dict, Any, Set
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on log levels.
    
    This filter allows matching message fields against standard log levels
    and syslog severity levels. It supports case-insensitive matching and
    can invert the match result.
    
    Configuration:
        - levels: List of levels to match (required)
        - field: Field to match against (default: "level")
        - invert: Whether to invert the match (default: False)
    """
    
    # Standard log levels with numeric values
    STANDARD_LEVELS = {
        "debug": 10,
        "info": 20,
        "warning": 30,
        "error": 40,
        "critical": 50
    }
    
    # Syslog severity levels with numeric values
    SYSLOG_LEVELS = {
        "emerg": 0,
        "alert": 1,
        "crit": 2,
        "err": 3,
        "warning": 4,
        "notice": 5,
        "info": 6,
        "debug": 7
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize level filter.
        
        Args:
            config: Configuration dictionary containing:
                - levels: List of levels to match
                - field: Field to match against (default: "level")
                - invert: Whether to invert the match (default: False)
                
        Raises:
            ValueError: If configuration is invalid
        """
        super().__init__(config)
        
        # Get and validate levels
        levels = config.get("levels", [])
        if not levels:
            raise ValueError("levels parameter is required")
        self._validate_list(levels, "levels")
        
        # Convert levels to lowercase and validate
        self.levels: Set[str] = {level.lower() for level in levels}
        valid_levels = set(self.STANDARD_LEVELS.keys()) | set(self.SYSLOG_LEVELS.keys())
        invalid_levels = self.levels - valid_levels
        if invalid_levels:
            raise ValueError(f"Invalid levels: {', '.join(invalid_levels)}")
        
        # Get and validate field
        self.field = config.get("field", "level")
        self._validate_string(self.field, "field")
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on log level.
        
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
                
            # Convert to string and lowercase
            if not isinstance(field_value, str):
                field_value = str(field_value)
            field_value = field_value.lower()
            
            # Check if level matches
            result = field_value in self.levels
            
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