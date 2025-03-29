"""
Configuration handling for PySyslog LFC
"""

import configparser
from typing import Dict, Any, Optional
from pathlib import Path

class Config(configparser.ConfigParser):
    """Extended ConfigParser with additional functionality"""
    
    def __init__(self):
        super().__init__(interpolation=None)
        self.optionxform = str  # Preserve case in option names
    
    def load_file(self, path: str) -> None:
        """Load configuration from a file"""
        if not Path(path).exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        self.read(path)
    
    def get(self, section: str, option: str, fallback: Any = None) -> Any:
        """Get a configuration value with type conversion"""
        try:
            value = super().get(section, option)
            # Convert common boolean strings
            if value.lower() in ("true", "yes", "on", "1"):
                return True
            if value.lower() in ("false", "no", "off", "0"):
                return False
            return value
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def get_flow_config(self, flow_name: str) -> Optional[Dict[str, str]]:
        """Get configuration for a specific flow"""
        section = f"flow.{flow_name}"
        if not self.has_section(section):
            return None
        return dict(self[section]) 