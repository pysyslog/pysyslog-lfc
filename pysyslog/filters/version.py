"""
Version filter component for PySyslog LFC
"""

import logging
import re
from typing import Dict, Any, Callable, Union, List, Tuple
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on version number comparisons.
    
    This filter allows comparing version number field values against specified values
    using various operators. It supports semantic versioning (SemVer), numeric
    versioning, and component-based comparisons.
    
    Configuration:
        - field: Field to compare (required)
        - operator: Version operator (required)
        - value: Version number to compare against (required)
        - format: Version format (semver or numeric, default: semver)
        - invert: Whether to invert the match (default: False)
    """
    
    # Version regex patterns
    SEMVER_PATTERN = re.compile(r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$')
    NUMERIC_PATTERN = re.compile(r'^(\d+)(?:\.(\d+))*$')
    
    # Valid operators and their functions
    OPERATORS = {
        # Version operators
        "equals": lambda x, y: x == y,
        "not_equals": lambda x, y: x != y,
        "greater_than": lambda x, y: x > y,
        "greater_than_or_equal": lambda x, y: x >= y,
        "less_than": lambda x, y: x < y,
        "less_than_or_equal": lambda x, y: x <= y,
        
        # Component operators
        "major_equals": lambda x, y: x[0] == y[0],
        "minor_equals": lambda x, y: x[1] == y[1],
        "patch_equals": lambda x, y: x[2] == y[2],
        
        # Validation operators
        "is_valid": lambda x, y: bool(x),
        "is_invalid": lambda x, y: not bool(x)
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize version filter.
        
        Args:
            config: Configuration dictionary containing:
                - field: Field to compare
                - operator: Version operator
                - value: Version number to compare against
                - format: Version format (semver or numeric, default: semver)
                - invert: Whether to invert the match (default: False)
                
        Raises:
            ValueError: If configuration is invalid
        """
        super().__init__(config)
        
        # Get and validate field
        self.field = config.get("field")
        if not self.field:
            raise ValueError("field parameter is required")
        self._validate_string(self.field, "field")
        
        # Get and validate operator
        self.operator = config.get("operator")
        if not self.operator:
            raise ValueError("operator parameter is required")
        if self.operator not in self.OPERATORS:
            raise ValueError(f"Invalid operator: {self.operator}. Must be one of: {', '.join(self.OPERATORS.keys())}")
        
        # Get and validate format
        self.format = config.get("format", "semver")
        if self.format not in ["semver", "numeric"]:
            raise ValueError("format must be either 'semver' or 'numeric'")
        
        # Get and validate value
        self.value = config.get("value")
        if self.value is None:
            raise ValueError("value parameter is required")
        self._validate_string(self.value, "value")
        
        # Parse value
        self.value = self._parse_version(self.value)
        if not self.value:
            raise ValueError(f"Invalid version format: {self.value}")
        
        # Get operator function
        self._operator_func = self.OPERATORS[self.operator]
    
    def _parse_version(self, version: str) -> Tuple[int, int, int]:
        """Parse version string into tuple of integers.
        
        Args:
            version: Version string to parse
            
        Returns:
            Tuple of (major, minor, patch) version numbers
        """
        if self.format == "semver":
            match = self.SEMVER_PATTERN.match(version)
            if match:
                return tuple(int(x) for x in match.groups()[:3])
        else:
            match = self.NUMERIC_PATTERN.match(version)
            if match:
                parts = [int(x) for x in match.groups() if x is not None]
                if len(parts) >= 3:
                    return tuple(parts[:3])
        return None
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on version comparison.
        
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
            
            # Parse version
            field_value = self._parse_version(field_value)
            if not field_value:
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