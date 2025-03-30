"""
Base filter component for PySyslog LFC
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Generic, TypeVar, Optional
from datetime import datetime
from enum import Enum

T = TypeVar('T')

class FilterStage(Enum):
    """Filter application stage"""
    INPUT = "input"
    PARSER = "parser"
    OUTPUT = "output"

class FilterComponent(ABC, Generic[T]):
    """Base class for filter components with common functionality.
    
    This class provides common functionality for all filter components:
    - Input validation
    - Type conversion
    - Error handling
    - Logging
    - Security limits
    
    All filter components must inherit from this class and implement the filter() method.
    Filters can only be used as part of a flow and must be configured with a flow name.
    """
    
    # Security limits
    MAX_PATTERN_LENGTH = 1000
    MAX_LIST_SIZE = 1000
    MAX_FIELD_LENGTH = 1000
    MAX_STRING_LENGTH = 10000
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize filter component.
        
        Args:
            config: Configuration dictionary containing:
                - flow_name: Name of the flow this filter belongs to (required)
                - type: Filter type (required)
                - field: Field to evaluate (required)
                - op: Operation to apply (required)
                - value: Value to compare (required)
                - min: Lower bound for range operations (optional)
                - max: Upper bound for range operations (optional)
                - pattern: Regex pattern for regex operations (optional)
                - stage: Where to apply the filter (default: parser)
                - enabled: Whether the filter is enabled (default: True)
                - invert: Whether to invert the match (default: False)
                
        Raises:
            ValueError: If configuration is invalid
        """
        self.logger = logging.getLogger(f"pysyslog.filter.{self.__class__.__name__}")
        
        # Get and validate flow name
        self.flow_name = config.get("flow_name")
        if not self.flow_name:
            raise ValueError("flow_name parameter is required")
        self._validate_string(self.flow_name, "flow_name")
        
        # Get and validate filter type
        self.type = config.get("type")
        if not self.type:
            raise ValueError("type parameter is required")
        self._validate_string(self.type, "type")
        
        # Get and validate field
        self.field = config.get("field")
        if not self.field:
            raise ValueError("field parameter is required")
        self._validate_string(self.field, "field")
        
        # Get and validate operation
        self.op = config.get("op")
        if not self.op:
            raise ValueError("op parameter is required")
        self._validate_string(self.op, "op")
        
        # Get and validate value
        self.value = config.get("value")
        if self.value is None:
            raise ValueError("value parameter is required")
        
        # Get optional parameters
        self.min_value = config.get("min")
        self.max_value = config.get("max")
        self.pattern = config.get("pattern")
        self.stage = FilterStage(config.get("stage", "parser"))
        self.enabled = bool(config.get("enabled", True))
        self.invert = bool(config.get("invert", False))
        
        # Initialize filter state
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the filter component.
        
        This method must be called by the flow before using the filter.
        It ensures the filter is properly configured and ready to use.
        
        Raises:
            RuntimeError: If filter is already initialized
        """
        if self._initialized:
            raise RuntimeError("Filter is already initialized")
        
        # Validate filter-specific configuration
        self._validate_config()
        
        self._initialized = True
        self.logger.info(f"Initialized {self.type} filter for flow: {self.flow_name}")
    
    def is_initialized(self) -> bool:
        """Check if filter is initialized.
        
        Returns:
            bool: True if filter is initialized, False otherwise
        """
        return self._initialized
    
    def _validate_config(self) -> None:
        """Validate filter-specific configuration.
        
        This method should be overridden by filter implementations to validate
        their specific configuration parameters.
        
        Raises:
            ValueError: If configuration is invalid
        """
        pass
    
    def _validate_string(self, value: str, param_name: str) -> None:
        """Validate string parameter.
        
        Args:
            value: String to validate
            param_name: Parameter name for error messages
            
        Raises:
            ValueError: If validation fails
        """
        if not isinstance(value, str):
            raise ValueError(f"{param_name} must be a string")
        if len(value) > self.MAX_STRING_LENGTH:
            raise ValueError(f"{param_name} exceeds maximum length of {self.MAX_STRING_LENGTH}")
    
    def _validate_list(self, value: list, param_name: str) -> None:
        """Validate list parameter.
        
        Args:
            value: List to validate
            param_name: Parameter name for error messages
            
        Raises:
            ValueError: If validation fails
        """
        if not isinstance(value, list):
            raise ValueError(f"{param_name} must be a list")
        if len(value) > self.MAX_LIST_SIZE:
            raise ValueError(f"{param_name} exceeds maximum size of {self.MAX_LIST_SIZE}")
        for item in value:
            if isinstance(item, str) and len(item) > self.MAX_STRING_LENGTH:
                raise ValueError(f"Item in {param_name} exceeds maximum length of {self.MAX_STRING_LENGTH}")
    
    def _validate_pattern(self, pattern: str) -> None:
        """Validate regex pattern.
        
        Args:
            pattern: Pattern to validate
            
        Raises:
            ValueError: If validation fails
        """
        if not isinstance(pattern, str):
            raise ValueError("Pattern must be a string")
        if len(pattern) > self.MAX_PATTERN_LENGTH:
            raise ValueError(f"Pattern exceeds maximum length of {self.MAX_PATTERN_LENGTH}")
        try:
            re.compile(pattern)
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
            
        Raises:
            RuntimeError: If filter is not initialized
        """
        if not self._initialized:
            raise RuntimeError("Filter is not initialized")
        if not self.enabled:
            return True
    
    def close(self) -> None:
        """Cleanup resources."""
        self._initialized = False
        self.logger.info(f"Closed {self.type} filter for flow: {self.flow_name}") 