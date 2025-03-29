"""
Passthrough parser component
"""

import json
from typing import Optional, Dict, Any

from ..components import ParserComponent

class Parser(ParserComponent):
    """Passthrough parser"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.format = config.get("format", "text")
    
    def parse(self, data: str) -> Optional[Dict[str, Any]]:
        """Pass through data with optional format conversion"""
        try:
            if self.format == "json":
                return json.loads(data)
            else:
                return {"message": data}
        except Exception as e:
            self.logger.error(f"Error parsing message: {e}")
            return None 