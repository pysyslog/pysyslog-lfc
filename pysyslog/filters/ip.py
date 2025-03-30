"""
IP address filter component for PySyslog LFC
"""

import logging
import ipaddress
from typing import Dict, Any, Callable, Union, List
from .base import FilterComponent, FilterStage

class Filter(FilterComponent):
    """Filter messages based on IP address comparisons.
    
    This filter allows comparing IP address field values against specified values
    using various operators. It supports IPv4 and IPv6 addresses, CIDR ranges,
    and network membership checks.
    
    Configuration:
        - field: Field to compare (required)
        - op: IP address operator (required)
        - value: IP address or CIDR range to compare against (required)
        - stage: Where to apply the filter (default: parser)
        - invert: Whether to invert the match (default: false)
    """
    
    # Valid operators and their functions
    OPERATORS = {
        # Basic operations
        "eq": lambda x, y: x == y,
        "ne": lambda x, y: x != y,
        
        # Network operations
        "in_network": lambda x, y: x in y,
        "not_in_network": lambda x, y: x not in y,
        
        # IP type operations
        "is_private": lambda x, y: x.is_private,
        "is_global": lambda x, y: x.is_global,
        "is_multicast": lambda x, y: x.is_multicast,
        "is_loopback": lambda x, y: x.is_loopback,
        "is_link_local": lambda x, y: x.is_link_local
    }
    
    # Security limits
    MAX_CIDR_PREFIX = 32  # Maximum CIDR prefix for IPv4
    MAX_CIDR_PREFIX_V6 = 128  # Maximum CIDR prefix for IPv6
    MAX_NETWORKS = 100  # Maximum number of networks in a list
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize IP address filter.
        
        Args:
            config: Configuration dictionary containing:
                - flow_name: Name of the flow this filter belongs to (required)
                - type: Filter type (required)
                - field: Field to compare (required)
                - op: IP address operator (required)
                - value: IP address or CIDR range to compare against (required)
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
            
        # Parse value based on operator
        if self.op in ["in_network", "not_in_network"]:
            try:
                self.value = ipaddress.ip_network(self.value)
                # Validate CIDR prefix
                if self.value.prefixlen > (self.MAX_CIDR_PREFIX_V6 if self.value.version == 6 else self.MAX_CIDR_PREFIX):
                    raise ValueError(f"CIDR prefix too large: {self.value.prefixlen}")
            except ValueError as e:
                raise ValueError(f"Invalid CIDR range: {e}")
        else:
            try:
                self.value = ipaddress.ip_address(self.value)
            except ValueError as e:
                raise ValueError(f"Invalid IP address: {e}")
        
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
        
        # Validate field value can be converted to IP address
        try:
            ipaddress.ip_address(self._test_data[self.field])
        except ValueError:
            raise ValueError(f"Field '{self.field}' must contain valid IP addresses")
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on IP address comparison.
        
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
            
            # Convert to IP address
            try:
                field_value = ipaddress.ip_address(field_value)
            except ValueError:
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