"""
Level filter component for PySyslog LFC
"""

from typing import Dict, Any, List, Optional
from ..components import FilterComponent

class Filter(FilterComponent):
    """Level filter component"""
    
    # Standard log levels
    STANDARD_LEVELS = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50
    }
    
    # Syslog levels
    SYSLOG_LEVELS = {
        "EMERG": 0,
        "ALERT": 1,
        "CRIT": 2,
        "ERR": 3,
        "WARNING": 4,
        "NOTICE": 5,
        "INFO": 6,
        "DEBUG": 7
    }
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.levels = config.get("levels", "").split(",")
        self.field = config.get("field", "level")
        self.invert = config.get("invert", False)
        
        if not self.levels or not self.levels[0]:
            raise ValueError("Levels are required for level filter")
        
        # Convert level names to values
        self.level_values = set()
        for level in self.levels:
            level = level.strip().upper()
            if level in self.STANDARD_LEVELS:
                self.level_values.add(self.STANDARD_LEVELS[level])
            elif level in self.SYSLOG_LEVELS:
                self.level_values.add(self.SYSLOG_LEVELS[level])
            else:
                raise ValueError(f"Unknown log level: {level}")
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on log level
        
        Args:
            data: Parsed message data
            
        Returns:
            bool: True if message level matches (or doesn't match if inverted)
        """
        try:
            # Get level value
            level = data.get(self.field)
            if not level:
                return False
            
            # Convert level to numeric value
            if isinstance(level, str):
                level = level.upper()
                if level in self.STANDARD_LEVELS:
                    level = self.STANDARD_LEVELS[level]
                elif level in self.SYSLOG_LEVELS:
                    level = self.SYSLOG_LEVELS[level]
                else:
                    return False
            
            # Check level match
            matches = level in self.level_values
            
            # Return based on invert setting
            return not matches if self.invert else matches
            
        except Exception as e:
            self.logger.error(f"Error filtering message: {e}")
            return False
    
    def close(self) -> None:
        """Cleanup resources"""
        pass 