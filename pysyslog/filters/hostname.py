"""
Hostname filter component for PySyslog LFC
"""

import logging
import re
from typing import Dict, Any, Callable, Union, List
from .base import FilterComponent, FilterStage

class Filter(FilterComponent):
    """Filter messages based on hostname comparisons.
    
    This filter allows comparing hostname field values against specified values
    using various operators. It supports hostname validation, domain checks,
    and component-based comparisons.
    
    Configuration:
        - field: Field to compare (required)
        - op: Hostname operator (required)
        - value: Hostname or hostname component to compare against (required)
        - component: Hostname component to compare (optional)
        - stage: Where to apply the filter (default: parser)
        - invert: Whether to invert the match (default: false)
    """
    
    # Hostname regex pattern
    HOSTNAME_PATTERN = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$')
    
    # Valid operators and their functions
    OPERATORS = {
        # Hostname operators
        "eq": lambda x, y: x == y,
        "ne": lambda x, y: x != y,
        "contains": lambda x, y: y in x,
        "not_contains": lambda x, y: y not in x,
        "starts_with": lambda x, y: x.startswith(y),
        "ends_with": lambda x, y: x.endswith(y),
        
        # Component operators
        "domain_eq": lambda x, y: x.split(".")[-2:] == y.split("."),
        "domain_ends_with": lambda x, y: x.endswith(y),
        "subdomain_eq": lambda x, y: x.split(".")[0] == y,
        
        # Validation operators
        "is_valid": lambda x, y: bool(Filter.HOSTNAME_PATTERN.match(x)),
        "is_invalid": lambda x, y: not bool(Filter.HOSTNAME_PATTERN.match(x)),
        
        # Special operators
        "is_ipv4": lambda x, y: bool(re.match(r'^(\d{1,3}\.){3}\d{1,3}$', x)),
        "is_ipv6": lambda x, y: bool(re.match(r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$', x)),
        "is_localhost": lambda x, y: x.lower() in ["localhost", "127.0.0.1", "::1"]
    }
    
    # Security limits
    MAX_HOSTNAME_LENGTH = 253  # Maximum hostname length (RFC 1035)
    MAX_LABEL_LENGTH = 63  # Maximum label length (RFC 1035)
    MAX_LABELS = 127  # Maximum number of labels (RFC 1035)
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize hostname filter.
        
        Args:
            config: Configuration dictionary containing:
                - flow_name: Name of the flow this filter belongs to (required)
                - type: Filter type (required)
                - field: Field to compare (required)
                - op: Hostname operator (required)
                - value: Hostname or hostname component to compare against (required)
                - component: Hostname component to compare (optional)
                - stage: Where to apply the filter (default: parser)
                - invert: Whether to invert the match (default: false)
                
        Raises:
            ValueError: If configuration is invalid
        """
        super().__init__(config)
        
        # Get and validate operator
        self.op = config.get("op")
        if not self.op:
            raise ValueError("op parameter is required")
        if self.op not in self.OPERATORS:
            raise ValueError(f"Invalid operator: {self.op}. Must be one of: {', '.join(self.OPERATORS.keys())}")
        
        # Get and validate value
        self.value = config.get("value")
        if self.value is None:
            raise ValueError("value parameter is required")
        self._validate_string(self.value, "value")
        
        # Validate value length
        if len(self.value) > self.MAX_HOSTNAME_LENGTH:
            raise ValueError(f"Hostname too long: {len(self.value)}")
        
        # Validate hostname if needed
        if self.op in ["domain_eq", "domain_ends_with", "subdomain_eq"]:
            if not self.HOSTNAME_PATTERN.match(self.value):
                raise ValueError(f"Invalid hostname: {self.value}")
            # Validate component lengths
            labels = self.value.split(".")
            if len(labels) > self.MAX_LABELS:
                raise ValueError("Too many labels")
            for label in labels:
                if len(label) > self.MAX_LABEL_LENGTH:
                    raise ValueError(f"Label too long: {len(label)}")
        
        # Get operator function
        self._operator_func = self.OPERATORS[self.op]
    
    def _validate_config(self) -> None:
        """Validate filter-specific configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate field exists in data
        if self.field not in self._test_data:
            raise ValueError(f"Field '{self.field}' not found in test data")
        
        # Validate field value can be parsed as hostname
        field_value = self._test_data[self.field]
        if isinstance(field_value, str):
            if len(field_value) > self.MAX_HOSTNAME_LENGTH:
                raise ValueError(f"Hostname too long: {len(field_value)}")
            if not self.HOSTNAME_PATTERN.match(field_value):
                raise ValueError(f"Field '{self.field}' must contain valid hostnames")
            # Validate component lengths
            labels = field_value.split(".")
            if len(labels) > self.MAX_LABELS:
                raise ValueError("Too many labels")
            for label in labels:
                if len(label) > self.MAX_LABEL_LENGTH:
                    raise ValueError(f"Label too long: {len(label)}")
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on hostname comparison.
        
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
            
            # Validate length
            if len(field_value) > self.MAX_HOSTNAME_LENGTH:
                return False
            
            # Validate hostname format
            if not self.HOSTNAME_PATTERN.match(field_value):
                return False
            
            # Validate component lengths
            labels = field_value.split(".")
            if len(labels) > self.MAX_LABELS:
                return False
            for label in labels:
                if len(label) > self.MAX_LABEL_LENGTH:
                    return False
            
            # Apply operator
            result = self._operator_func(field_value, self.value)
            
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