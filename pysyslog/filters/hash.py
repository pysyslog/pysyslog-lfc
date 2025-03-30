"""
Hash filter component for PySyslog LFC
"""

import logging
import re
import hashlib
from typing import Dict, Any, Callable, Union, List
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on hash value comparisons.
    
    This filter allows comparing hash field values against specified values
    using various operators. It supports multiple hash algorithms and
    format validation.
    
    Configuration:
        - field: Field to compare (required)
        - operator: Hash operator (required)
        - value: Hash value to compare against (required)
        - algorithm: Hash algorithm (md5, sha1, sha256, sha512, default: sha256)
        - invert: Whether to invert the match (default: False)
    """
    
    # Hash regex patterns
    HASH_PATTERNS = {
        "md5": re.compile(r'^[a-f0-9]{32}$'),
        "sha1": re.compile(r'^[a-f0-9]{40}$'),
        "sha256": re.compile(r'^[a-f0-9]{64}$'),
        "sha512": re.compile(r'^[a-f0-9]{128}$')
    }
    
    # Hash functions
    HASH_FUNCTIONS = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512
    }
    
    # Valid operators and their functions
    OPERATORS = {
        # Hash operators
        "equals": lambda x, y: x == y,
        "not_equals": lambda x, y: x != y,
        "contains": lambda x, y: y in x,
        "not_contains": lambda x, y: y not in x,
        
        # Validation operators
        "is_valid": lambda x, y: bool(x),
        "is_invalid": lambda x, y: not bool(x)
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize hash filter.
        
        Args:
            config: Configuration dictionary containing:
                - field: Field to compare
                - operator: Hash operator
                - value: Hash value to compare against
                - algorithm: Hash algorithm (md5, sha1, sha256, sha512, default: sha256)
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
        
        # Get and validate algorithm
        self.algorithm = config.get("algorithm", "sha256")
        if self.algorithm not in self.HASH_PATTERNS:
            raise ValueError(f"Invalid algorithm: {self.algorithm}. Must be one of: {', '.join(self.HASH_PATTERNS.keys())}")
        
        # Get and validate value
        self.value = config.get("value")
        if self.value is None:
            raise ValueError("value parameter is required")
        self._validate_string(self.value, "value")
        
        # Validate hash format
        if not self.HASH_PATTERNS[self.algorithm].match(self.value):
            raise ValueError(f"Invalid {self.algorithm} hash format: {self.value}")
        
        # Get operator function
        self._operator_func = self.OPERATORS[self.operator]
    
    def _compute_hash(self, data: str) -> str:
        """Compute hash of input data.
        
        Args:
            data: Input data to hash
            
        Returns:
            Computed hash value
        """
        hash_func = self.HASH_FUNCTIONS[self.algorithm]
        return hash_func(data.encode()).hexdigest()
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on hash comparison.
        
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
            
            # Compute hash if needed
            if self.operator not in ["is_valid", "is_invalid"]:
                field_value = self._compute_hash(field_value)
            
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