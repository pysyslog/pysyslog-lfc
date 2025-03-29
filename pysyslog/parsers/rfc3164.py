"""
RFC 3164 syslog parser component
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any

from ..components import ParserComponent

class Parser(ParserComponent):
    """RFC 3164 syslog parser"""
    
    # RFC 3164 format: <PRI>TIMESTAMP HOSTNAME TAG: MSG
    PATTERN = re.compile(
        r"<(\d+)>"
        r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"
        r"\s+(\S+)"
        r"\s+(\S+):"
        r"\s+(.*)"
    )
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.time_format = config.get("time_format", "%b %d %H:%M:%S")
    
    def parse(self, data: str) -> Optional[Dict[str, Any]]:
        """Parse RFC 3164 syslog message"""
        match = self.PATTERN.match(data)
        if not match:
            return None
        
        try:
            pri, timestamp, hostname, tag, msg = match.groups()
            
            # Parse priority
            priority = int(pri)
            facility = priority >> 3
            severity = priority & 0x7
            
            # Parse timestamp
            year = datetime.now().year
            timestamp_str = f"{year} {timestamp}"
            timestamp_dt = datetime.strptime(timestamp_str, f"%Y {self.time_format}")
            
            return {
                "timestamp": timestamp_dt.isoformat(),
                "hostname": hostname,
                "tag": tag,
                "message": msg,
                "facility": facility,
                "severity": severity,
                "priority": priority
            }
        except Exception as e:
            self.logger.error(f"Error parsing message: {e}")
            return None 