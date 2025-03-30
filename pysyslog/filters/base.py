"""
Base filter component for PySyslog LFC
"""

import logging
import re
from typing import Dict, Any, Optional, Callable, TypeVar, Generic
from abc import ABC, abstractmethod
from datetime import datetime

T = TypeVar('T')

class FilterComponent(ABC, Generic[T]):
    """Base class for filter components with common functionality"""
    
    # Security limits
    MAX_PATTERN_LENGTH = 1000
    MAX_LIST_SIZE = 1000
    MAX_FIELD_LENGTH = 100
    MAX_STRING_LENGTH = 10000
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize filter component.
        
        Args:
            config: Configuration dictionary containing filter parameters
            
        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._validate_config(config)
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate configuration parameters.
        
        Args:
            config: Configuration dictionary to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")
            
        # Validate field name
        field = config.get("field")
        if not field or not isinstance(field, str):
            raise ValueError("Field name is required and must be a string")
        if len(field) > self.MAX_FIELD_LENGTH:
            raise ValueError(f"Field name too long (max {self.MAX_FIELD_LENGTH} chars)")
            
        # Validate invert parameter
        self.invert = bool(config.get("invert", False))
    
    def _validate_string(self, value: str, param_name: str) -> None:
        """Validate string parameter.
        
        Args:
            value: String value to validate
            param_name: Name of the parameter for error messages
            
        Raises:
            ValueError: If string is invalid
        """
        if not isinstance(value, str):
            raise ValueError(f"{param_name} must be a string")
        if len(value) > self.MAX_STRING_LENGTH:
            raise ValueError(f"{param_name} too long (max {self.MAX_STRING_LENGTH} chars)")
    
    def _validate_list(self, value: list, param_name: str) -> None:
        """Validate list parameter.
        
        Args:
            value: List value to validate
            param_name: Name of the parameter for error messages
            
        Raises:
            ValueError: If list is invalid
        """
        if not isinstance(value, list):
            raise ValueError(f"{param_name} must be a list")
        if len(value) > self.MAX_LIST_SIZE:
            raise ValueError(f"{param_name} too large (max {self.MAX_LIST_SIZE} items)")
    
    def _compile_pattern(self, pattern: str) -> re.Pattern:
        """Compile regex pattern with security checks.
        
        Args:
            pattern: Regex pattern to compile
            
        Returns:
            Compiled regex pattern
            
        Raises:
            ValueError: If pattern is invalid
        """
        if len(pattern) > self.MAX_PATTERN_LENGTH:
            raise ValueError(f"Pattern too long (max {self.MAX_PATTERN_LENGTH} chars)")
        try:
            return re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
    
    def _convert_to_datetime(self, value: str, format: str) -> datetime:
        """Convert string to datetime with validation.
        
        Args:
            value: String to convert
            format: Datetime format string
            
        Returns:
            Datetime object
            
        Raises:
            ValueError: If conversion fails
        """
        try:
            return datetime.strptime(value, format)
        except ValueError as e:
            raise ValueError(f"Invalid datetime format: {e}")
    
    def _convert_to_float(self, value: Any) -> float:
        """Convert value to float with validation.
        
        Args:
            value: Value to convert
            
        Returns:
            Float value
            
        Raises:
            ValueError: If conversion fails
        """
        try:
            result = float(value)
            if not -1e308 <= result <= 1e308:
                raise ValueError("Value out of range")
            return result
        except (ValueError, TypeError):
            raise ValueError(f"Invalid numeric value: {value}")
    
    def _convert_to_bool(self, value: Any) -> bool:
        """Convert value to boolean with validation.
        
        Args:
            value: Value to convert
            
        Returns:
            Boolean value
            
        Raises:
            ValueError: If conversion fails
        """
        if isinstance(value, str):
            return value.lower() in ["true", "1", "yes", "on"]
        if isinstance(value, (bool, int)):
            return bool(value)
        raise ValueError(f"Invalid boolean value: {value}")
    
    @abstractmethod
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter parsed data.
        
        Args:
            data: Parsed message data
            
        Returns:
            bool: True if message should be kept, False if filtered out
        """
        pass
    
    def close(self) -> None:
        """Cleanup resources."""
        pass 