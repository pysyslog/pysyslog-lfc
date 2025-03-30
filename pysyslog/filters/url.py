"""
URL filter component for PySyslog LFC
"""

import logging
from urllib.parse import urlparse, urlunparse
from typing import Dict, Any, Callable, Union, List
from .base import FilterComponent, FilterStage

class Filter(FilterComponent):
    """Filter messages based on URL comparisons.
    
    This filter allows comparing URL field values against specified values
    using various operators. It supports URL parsing, validation, and
    component-based comparisons.
    
    Configuration:
        - field: Field to compare (required)
        - op: URL operator (required)
        - value: URL or URL component to compare against (required)
        - component: URL component to compare (optional)
        - stage: Where to apply the filter (default: parser)
        - invert: Whether to invert the match (default: false)
    """
    
    # Valid operators and their functions
    OPERATORS = {
        # URL operators
        "eq": lambda x, y: x == y,
        "ne": lambda x, y: x != y,
        "contains": lambda x, y: y in x,
        "not_contains": lambda x, y: y not in x,
        "starts_with": lambda x, y: x.startswith(y),
        "ends_with": lambda x, y: x.endswith(y),
        
        # Component operators
        "scheme_eq": lambda x, y: x.scheme == y,
        "netloc_eq": lambda x, y: x.netloc == y,
        "path_eq": lambda x, y: x.path == y,
        "query_eq": lambda x, y: x.query == y,
        "fragment_eq": lambda x, y: x.fragment == y,
        
        # Validation operators
        "is_valid": lambda x, y: bool(x.scheme and x.netloc),
        "is_secure": lambda x, y: x.scheme in ["https", "wss"],
        "is_absolute": lambda x, y: bool(x.scheme),
        "is_relative": lambda x, y: not x.scheme
    }
    
    # Security limits
    MAX_URL_LENGTH = 2000  # Maximum URL length
    MAX_COMPONENT_LENGTH = 1000  # Maximum component length
    MAX_SCHEMES = 10  # Maximum number of schemes to check
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize URL filter.
        
        Args:
            config: Configuration dictionary containing:
                - flow_name: Name of the flow this filter belongs to (required)
                - type: Filter type (required)
                - field: Field to compare (required)
                - op: URL operator (required)
                - value: URL or URL component to compare against (required)
                - component: URL component to compare (optional)
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
        if len(self.value) > self.MAX_URL_LENGTH:
            raise ValueError(f"URL too long: {len(self.value)}")
        
        # Parse value if it's a URL
        if self.op in ["scheme_eq", "netloc_eq", "path_eq", 
                      "query_eq", "fragment_eq", "is_valid",
                      "is_secure", "is_absolute", "is_relative"]:
            try:
                self.value = urlparse(self.value)
                # Validate component lengths
                for component in [self.value.scheme, self.value.netloc, 
                                self.value.path, self.value.query, 
                                self.value.fragment]:
                    if component and len(component) > self.MAX_COMPONENT_LENGTH:
                        raise ValueError(f"URL component too long: {len(component)}")
            except Exception as e:
                raise ValueError(f"Invalid URL: {e}")
        
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
        
        # Validate field value can be parsed as URL
        field_value = self._test_data[self.field]
        if isinstance(field_value, str):
            if len(field_value) > self.MAX_URL_LENGTH:
                raise ValueError(f"URL too long: {len(field_value)}")
            try:
                parsed = urlparse(field_value)
                # Validate component lengths
                for component in [parsed.scheme, parsed.netloc, 
                                parsed.path, parsed.query, 
                                parsed.fragment]:
                    if component and len(component) > self.MAX_COMPONENT_LENGTH:
                        raise ValueError(f"URL component too long: {len(component)}")
            except Exception:
                raise ValueError(f"Field '{self.field}' must contain valid URLs")
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on URL comparison.
        
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
            if len(field_value) > self.MAX_URL_LENGTH:
                return False
            
            # Parse URL if needed
            if self.op in ["scheme_eq", "netloc_eq", "path_eq", 
                          "query_eq", "fragment_eq", "is_valid",
                          "is_secure", "is_absolute", "is_relative"]:
                try:
                    field_value = urlparse(field_value)
                    # Validate component lengths
                    for component in [field_value.scheme, field_value.netloc, 
                                    field_value.path, field_value.query, 
                                    field_value.fragment]:
                        if component and len(component) > self.MAX_COMPONENT_LENGTH:
                            return False
                except Exception:
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