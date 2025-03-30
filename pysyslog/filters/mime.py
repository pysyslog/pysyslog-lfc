"""
MIME type filter component for PySyslog LFC
"""

import logging
import mimetypes
from typing import Dict, Any, Callable, Union, List
from .base import FilterComponent

class Filter(FilterComponent):
    """Filter messages based on MIME type comparisons.
    
    This filter allows comparing MIME type field values against specified values
    using various operators. It supports MIME type validation, category checks,
    and common MIME type comparisons.
    
    Configuration:
        - field: Field to compare (required)
        - operator: MIME type operator (required)
        - value: MIME type to compare against (required)
        - invert: Whether to invert the match (default: False)
    """
    
    # MIME type categories
    MIME_CATEGORIES = {
        "text": ["text/plain", "text/html", "text/css", "text/javascript", "text/xml"],
        "image": ["image/jpeg", "image/png", "image/gif", "image/svg+xml", "image/webp"],
        "audio": ["audio/mpeg", "audio/ogg", "audio/wav", "audio/webm"],
        "video": ["video/mp4", "video/webm", "video/ogg", "video/quicktime"],
        "application": ["application/json", "application/xml", "application/pdf", "application/zip", "application/x-tar"],
        "multipart": ["multipart/form-data", "multipart/mixed", "multipart/alternative"],
        "message": ["message/rfc822", "message/delivery-status", "message/disposition-notification"],
        "font": ["font/ttf", "font/otf", "font/woff", "font/woff2"]
    }
    
    # Common MIME types with their extensions
    COMMON_MIME_TYPES = {
        # Text
        "text/plain": "txt",
        "text/html": "html",
        "text/css": "css",
        "text/javascript": "js",
        "text/xml": "xml",
        
        # Image
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "image/svg+xml": "svg",
        "image/webp": "webp",
        
        # Audio
        "audio/mpeg": "mp3",
        "audio/ogg": "ogg",
        "audio/wav": "wav",
        "audio/webm": "webm",
        
        # Video
        "video/mp4": "mp4",
        "video/webm": "webm",
        "video/ogg": "ogv",
        "video/quicktime": "mov",
        
        # Application
        "application/json": "json",
        "application/xml": "xml",
        "application/pdf": "pdf",
        "application/zip": "zip",
        "application/x-tar": "tar",
        "application/x-rar-compressed": "rar",
        "application/x-7z-compressed": "7z",
        "application/x-bzip2": "bz2",
        "application/x-gzip": "gz",
        
        # Multipart
        "multipart/form-data": None,
        "multipart/mixed": None,
        "multipart/alternative": None,
        
        # Message
        "message/rfc822": "eml",
        "message/delivery-status": None,
        "message/disposition-notification": None,
        
        # Font
        "font/ttf": "ttf",
        "font/otf": "otf",
        "font/woff": "woff",
        "font/woff2": "woff2"
    }
    
    # Valid operators and their functions
    OPERATORS = {
        # MIME type operators
        "equals": lambda x, y: x == y,
        "not_equals": lambda x, y: x != y,
        "contains": lambda x, y: y in x,
        "not_contains": lambda x, y: y not in x,
        
        # Category operators
        "in_category": lambda x, y: x in Filter.MIME_CATEGORIES[y],
        "not_in_category": lambda x, y: x not in Filter.MIME_CATEGORIES[y],
        
        # Validation operators
        "is_valid": lambda x, y: bool(x),
        "is_invalid": lambda x, y: not bool(x),
        
        # Special operators
        "is_text": lambda x, y: x.startswith("text/"),
        "is_image": lambda x, y: x.startswith("image/"),
        "is_audio": lambda x, y: x.startswith("audio/"),
        "is_video": lambda x, y: x.startswith("video/"),
        "is_application": lambda x, y: x.startswith("application/"),
        "is_multipart": lambda x, y: x.startswith("multipart/"),
        "is_message": lambda x, y: x.startswith("message/"),
        "is_font": lambda x, y: x.startswith("font/")
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize MIME type filter.
        
        Args:
            config: Configuration dictionary containing:
                - field: Field to compare
                - operator: MIME type operator
                - value: MIME type to compare against
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
        self._validate_string(self.value, "value")
        
        # Validate MIME type if needed
        if self.operator in ["in_category", "not_in_category"]:
            if self.value not in self.MIME_CATEGORIES:
                raise ValueError(f"Invalid MIME category: {self.value}")
        elif self.operator not in ["is_valid", "is_invalid"]:
            if self.value not in self.COMMON_MIME_TYPES:
                raise ValueError(f"Invalid MIME type: {self.value}")
        
        # Get operator function
        self._operator_func = self.OPERATORS[self.operator]
    
    def filter(self, data: Dict[str, Any]) -> bool:
        """Filter messages based on MIME type comparison.
        
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
            
            # Convert to lowercase
            field_value = field_value.lower()
            
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