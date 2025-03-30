"""
RFC 3164 syslog parser component with enhanced validation and format support
"""

import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
from ..components import ParserComponent

class Parser(ParserComponent):
    """RFC 3164 syslog parser with enhanced validation"""
    
    # RFC 3164 format patterns
    PATTERNS = {
        'standard': re.compile(
            r"<(\d+)>"
            r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"
            r"\s+(\S+)"
            r"\s+(\S+):"
            r"\s+(.*)"
        ),
        'without_tag': re.compile(
            r"<(\d+)>"
            r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"
            r"\s+(\S+)"
            r"\s+(.*)"
        ),
        'bsd': re.compile(
            r"<(\d+)>"
            r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"
            r"\s+(\S+)"
            r"\s+(\S+)\s+(\S+):"
            r"\s+(.*)"
        )
    }
    
    # Month abbreviations to numbers
    MONTHS = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
        'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
        'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
    
    # Common timezone offsets (in minutes)
    TIMEZONE_OFFSETS = {
        'UTC': 0,
        'GMT': 0,
        'EST': -300,  # -5 hours
        'EDT': -240,  # -4 hours
        'CST': -360,  # -6 hours
        'CDT': -300,  # -5 hours
        'MST': -420,  # -7 hours
        'MDT': -360,  # -6 hours
        'PST': -480,  # -8 hours
        'PDT': -420,  # -7 hours
    }
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.time_format = config.get("time_format", "%b %d %H:%M:%S")
        self.timezone = config.get("timezone", "UTC")
        self.validate_priority = config.get("validate_priority", True)
        self.validate_facility = config.get("validate_facility", True)
        self.validate_severity = config.get("validate_severity", True)
        self.max_message_length = config.get("max_message_length", 1024)
    
    def parse(self, data: str) -> Optional[Dict[str, Any]]:
        """Parse RFC 3164 syslog message with validation"""
        try:
            # Validate input length
            if len(data) > self.max_message_length:
                self.logger.warning(f"Message exceeds maximum length: {len(data)} > {self.max_message_length}")
                return None
            
            # Try different patterns
            match = None
            for pattern_name, pattern in self.PATTERNS.items():
                match = pattern.match(data)
                if match:
                    break
            
            if not match:
                self.logger.warning("Message does not match any known format")
                return None
            
            # Parse components based on pattern
            if pattern_name == 'standard':
                pri, timestamp, hostname, tag, msg = match.groups()
            elif pattern_name == 'without_tag':
                pri, timestamp, hostname, msg = match.groups()
                tag = None
            else:  # bsd
                pri, timestamp, hostname, program, pid, msg = match.groups()
                tag = f"{program}[{pid}]"
            
            # Parse and validate priority
            priority = int(pri)
            if self.validate_priority and not (0 <= priority <= 191):
                self.logger.warning(f"Invalid priority value: {priority}")
                return None
            
            # Parse facility and severity
            facility = priority >> 3
            severity = priority & 0x7
            
            # Validate facility and severity
            if self.validate_facility and not (0 <= facility <= 23):
                self.logger.warning(f"Invalid facility value: {facility}")
                return None
            if self.validate_severity and not (0 <= severity <= 7):
                self.logger.warning(f"Invalid severity value: {severity}")
                return None
            
            # Parse timestamp
            timestamp_dt = self._parse_timestamp(timestamp)
            if not timestamp_dt:
                return None
            
            # Create result dictionary
            result = {
                "timestamp": timestamp_dt.isoformat(),
                "hostname": hostname,
                "message": msg,
                "facility": facility,
                "severity": severity,
                "priority": priority
            }
            
            # Add optional fields
            if tag:
                result["tag"] = tag
            
            # Add metadata
            result["parser"] = "rfc3164"
            result["format"] = pattern_name
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing message: {e}")
            return None
    
    def _parse_timestamp(self, timestamp: str) -> Optional[datetime]:
        """Parse timestamp with timezone support using built-in modules"""
        try:
            # Split timestamp components
            month_abbr, day, time_str = timestamp.split()
            month = self.MONTHS.get(month_abbr)
            if not month:
                self.logger.warning(f"Invalid month abbreviation: {month_abbr}")
                return None
            
            # Parse time components
            hour, minute, second = map(int, time_str.split(':'))
            
            # Get current year
            year = datetime.now().year
            
            # Create datetime object
            dt = datetime(year, month, day, hour, minute, second)
            
            # Apply timezone
            if self.timezone != "UTC":
                # Try to get offset from common timezones
                offset_minutes = self.TIMEZONE_OFFSETS.get(self.timezone)
                if offset_minutes is not None:
                    # Create timezone with offset
                    tz = timezone(timedelta(minutes=offset_minutes))
                    dt = dt.replace(tzinfo=tz)
                else:
                    # Fall back to UTC if timezone not found
                    self.logger.warning(f"Unknown timezone {self.timezone}, using UTC")
                    dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.replace(tzinfo=timezone.utc)
            
            return dt
            
        except Exception as e:
            self.logger.error(f"Error parsing timestamp: {e}")
            return None 