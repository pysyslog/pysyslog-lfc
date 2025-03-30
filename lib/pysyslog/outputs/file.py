"""
File output component
"""

import json
import os
from typing import Dict, Any
from datetime import datetime

from ..components import OutputComponent

class Output(OutputComponent):
    """File output component"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.file_path = config.get("path")
        self.encoding = config.get("encoding", "utf-8")
        self.format = config.get("format", "json")  # json or text
        self.rotate = config.get("rotate", True)
        self.max_size = config.get("max_size", 10 * 1024 * 1024)  # 10MB default
        self.max_files = config.get("max_files", 5)
        
        if not self.file_path:
            raise ValueError("File path is required")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
    
    def write(self, data: Dict[str, Any]) -> None:
        """Write data to file"""
        try:
            # Check if rotation is needed
            if self.rotate and os.path.exists(self.file_path):
                if os.path.getsize(self.file_path) >= self.max_size:
                    self._rotate_file()
            
            # Format the data
            if self.format == "json":
                output = json.dumps(data, default=str) + "\n"
            else:
                # Text format with timestamp
                timestamp = datetime.now().isoformat()
                output = f"[{timestamp}] {data.get('message', '')}\n"
            
            # Write to file
            with open(self.file_path, "a", encoding=self.encoding) as f:
                f.write(output)
        except Exception as e:
            self.logger.error(f"Error writing to file: {e}")
    
    def _rotate_file(self) -> None:
        """Rotate log files"""
        try:
            # Remove oldest file if it exists
            oldest_file = f"{self.file_path}.{self.max_files}"
            if os.path.exists(oldest_file):
                os.remove(oldest_file)
            
            # Rotate existing files
            for i in range(self.max_files - 1, 0, -1):
                old_file = f"{self.file_path}.{i}"
                new_file = f"{self.file_path}.{i + 1}"
                if os.path.exists(old_file):
                    os.rename(old_file, new_file)
            
            # Rename current file
            os.rename(self.file_path, f"{self.file_path}.1")
        except Exception as e:
            self.logger.error(f"Error rotating log files: {e}")
    
    def close(self) -> None:
        """Cleanup resources"""
        pass  # No cleanup needed for file output 