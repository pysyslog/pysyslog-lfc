"""
Email filter component for PySyslog LFC
"""

import logging
import re
from typing import Dict, Any, Callable, Union, List
from .base import FilterComponent, FilterStage

class Filter(FilterComponent):
    """Filter messages based on email address comparisons.
    
    This filter allows comparing email field values against specified values
    using various operators. It supports email validation, domain checks,
    and component-based comparisons.
    
    Configuration:
        - field: Field to compare (required)
        - op: Email operator (required)
        - value: Email or email component to compare against (required)
        - component: Email component to compare (optional)
        - stage: Where to apply the filter (default: parser)
        - invert: Whether to invert the match (default: false)
    """
    
    # Email regex pattern
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    # Valid operators and their functions
    OPERATORS = {
        # Email operators
        "eq": lambda x, y: x == y,
        "ne": lambda x, y: x != y,
        "contains": lambda x, y: y in x,
        "not_contains": lambda x, y: y not in x,
        "starts_with": lambda x, y: x.startswith(y),
        "ends_with": lambda x, y: x.endswith(y),
        
        # Component operators
        "local_part_eq": lambda x, y: x.split("@")[0] == y,
        "domain_eq": lambda x, y: x.split("@")[1] == y,
        "domain_ends_with": lambda x, y: x.split("@")[1].endswith(y),
        
        # Validation operators
        "is_valid": lambda x, y: bool(Filter.EMAIL_PATTERN.match(x)),
        "is_invalid": lambda x, y: not bool(Filter.EMAIL_PATTERN.match(x))
    }
    
    # Security limits
    MAX_EMAIL_LENGTH = 254  # Maximum email length (RFC 5321)
    MAX_LOCAL_PART_LENGTH = 64  # Maximum local part length (RFC 5321)
    MAX_DOMAIN_LENGTH = 255  # Maximum domain length (RFC 5321)
    MAX_DOMAIN_LABELS = 127  # Maximum number of domain labels (RFC 1035)
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize email filter.
        
        Args:
            config: Configuration dictionary containing:
                - flow_name: Name of the flow this filter belongs to (required)
                - type: Filter type (required)
                - field: Field to compare (required)
                - op: Email operator (required)
                - value: Email or email component to compare against (required)
                - component: Email component to compare (optional)
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
        if len(self.value) > self.MAX_EMAIL_LENGTH:
            raise ValueError(f"Email too long: {len(self.value)}")
        
        # Validate email if needed
        if self.op in ["local_part_eq", "domain_eq", "domain_ends_with"]:
            if not self.EMAIL_PATTERN.match(self.value):
                raise ValueError(f"Invalid email address: {self.value}")
            # Validate component lengths
            local_part, domain = self.value.split("@")
            if len(local_part) > self.MAX_LOCAL_PART_LENGTH:
                raise ValueError(f"Local part too long: {len(local_part)}")
            if len(domain) > self.MAX_DOMAIN_LENGTH:
                raise ValueError(f"Domain too long: {len(domain)}")
            if len(domain.split(".")) > self.MAX_DOMAIN_LABELS:
                raise ValueError("Too many domain labels")
        
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
        
        # Validate field value can be parsed as email
        field_value = self._test_data[self.field]
        if isinstance(field_value, str):
            if len(field_value) > self.MAX_EMAIL_LENGTH:
                raise ValueError(f"Email too long: {len(field_value)}")
            if not self.EMAIL_PATTERN.match(field_value):
                raise ValueError(f"Field '{self.field}' must contain valid email addresses")
            # Validate component lengths
            local_part, domain = field_value.split("@")
            if len(local_part) > self.MAX_LOCAL_PART_LENGTH:
                raise ValueError(f"Local part too long: {len(local_part)}")
            if len(domain) > self.MAX_DOMAIN_LENGTH:
                raise ValueError(f"Domain too long: {len(domain)}")
            if len(domain.split(".")) > self.MAX_DOMAIN_LABELS:
                raise ValueError("Too many domain labels")
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on email comparison.
        
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
            if len(field_value) > self.MAX_EMAIL_LENGTH:
                return False
            
            # Validate email format
            if not self.EMAIL_PATTERN.match(field_value):
                return False
            
            # Validate component lengths
            local_part, domain = field_value.split("@")
            if len(local_part) > self.MAX_LOCAL_PART_LENGTH:
                return False
            if len(domain) > self.MAX_DOMAIN_LENGTH:
                return False
            if len(domain.split(".")) > self.MAX_DOMAIN_LABELS:
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