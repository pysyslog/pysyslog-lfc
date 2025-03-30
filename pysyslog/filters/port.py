"""
Port filter component for PySyslog LFC
"""

import logging
from typing import Dict, Any, Callable, Union, List
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on port number comparisons.
    
    This filter allows comparing port number field values against specified values
    using various operators. It supports port validation, range checks,
    and well-known port comparisons.
    
    Configuration:
        - field: Field to compare (required)
        - operator: Port operator (required)
        - value: Port number or range to compare against (required)
        - invert: Whether to invert the match (default: False)
    """
    
    # Well-known port ranges
    PORT_RANGES = {
        "well_known": (0, 1023),
        "registered": (1024, 49151),
        "dynamic": (49152, 65535)
    }
    
    # Common well-known ports
    WELL_KNOWN_PORTS = {
        "ftp": 21,
        "ssh": 22,
        "telnet": 23,
        "smtp": 25,
        "dns": 53,
        "http": 80,
        "pop3": 110,
        "imap": 143,
        "https": 443,
        "smtp_submit": 587,
        "imap_ssl": 993,
        "pop3_ssl": 995,
        "mysql": 3306,
        "postgresql": 5432,
        "redis": 6379,
        "mongodb": 27017
    }
    
    # Valid operators and their functions
    OPERATORS = {
        # Port operators
        "equals": lambda x, y: x == y,
        "not_equals": lambda x, y: x != y,
        "greater_than": lambda x, y: x > y,
        "greater_than_or_equal": lambda x, y: x >= y,
        "less_than": lambda x, y: x < y,
        "less_than_or_equal": lambda x, y: x <= y,
        
        # Range operators
        "in_range": lambda x, y: y[0] <= x <= y[1],
        "not_in_range": lambda x, y: not (y[0] <= x <= y[1]),
        
        # Port range operators
        "is_well_known": lambda x, y: Filter.PORT_RANGES["well_known"][0] <= x <= Filter.PORT_RANGES["well_known"][1],
        "is_registered": lambda x, y: Filter.PORT_RANGES["registered"][0] <= x <= Filter.PORT_RANGES["registered"][1],
        "is_dynamic": lambda x, y: Filter.PORT_RANGES["dynamic"][0] <= x <= Filter.PORT_RANGES["dynamic"][1],
        
        # Well-known port operators
        "is_ftp": lambda x, y: x == Filter.WELL_KNOWN_PORTS["ftp"],
        "is_ssh": lambda x, y: x == Filter.WELL_KNOWN_PORTS["ssh"],
        "is_telnet": lambda x, y: x == Filter.WELL_KNOWN_PORTS["telnet"],
        "is_smtp": lambda x, y: x == Filter.WELL_KNOWN_PORTS["smtp"],
        "is_dns": lambda x, y: x == Filter.WELL_KNOWN_PORTS["dns"],
        "is_http": lambda x, y: x == Filter.WELL_KNOWN_PORTS["http"],
        "is_pop3": lambda x, y: x == Filter.WELL_KNOWN_PORTS["pop3"],
        "is_imap": lambda x, y: x == Filter.WELL_KNOWN_PORTS["imap"],
        "is_https": lambda x, y: x == Filter.WELL_KNOWN_PORTS["https"],
        "is_smtp_submit": lambda x, y: x == Filter.WELL_KNOWN_PORTS["smtp_submit"],
        "is_imap_ssl": lambda x, y: x == Filter.WELL_KNOWN_PORTS["imap_ssl"],
        "is_pop3_ssl": lambda x, y: x == Filter.WELL_KNOWN_PORTS["pop3_ssl"],
        "is_mysql": lambda x, y: x == Filter.WELL_KNOWN_PORTS["mysql"],
        "is_postgresql": lambda x, y: x == Filter.WELL_KNOWN_PORTS["postgresql"],
        "is_redis": lambda x, y: x == Filter.WELL_KNOWN_PORTS["redis"],
        "is_mongodb": lambda x, y: x == Filter.WELL_KNOWN_PORTS["mongodb"]
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize port filter.
        
        Args:
            config: Configuration dictionary containing:
                - field: Field to compare
                - operator: Port operator
                - value: Port number or range to compare against
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
        
        # Get and validate value
        self.value = config.get("value")
        if self.value is None:
            raise ValueError("value parameter is required")
        
        # Parse value based on operator
        if self.operator in ["in_range", "not_in_range"]:
            if not isinstance(self.value, list) or len(self.value) != 2:
                raise ValueError("Value must be a list of two port numbers for range operators")
            try:
                self.value = [int(x) for x in self.value]
                if not all(0 <= x <= 65535 for x in self.value):
                    raise ValueError("Port numbers must be between 0 and 65535")
                if self.value[0] > self.value[1]:
                    raise ValueError("Invalid port range: start port must be less than or equal to end port")
            except (ValueError, TypeError):
                raise ValueError("Invalid port range values")
        else:
            try:
                self.value = int(self.value)
                if not 0 <= self.value <= 65535:
                    raise ValueError("Port number must be between 0 and 65535")
            except (ValueError, TypeError):
                raise ValueError("Invalid port number")
        
        # Get operator function
        self._operator_func = self.OPERATORS[self.operator]
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on port comparison.
        
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
            
            # Convert to integer
            try:
                field_value = int(field_value)
                if not 0 <= field_value <= 65535:
                    return False
            except (ValueError, TypeError):
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