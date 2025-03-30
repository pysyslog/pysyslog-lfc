"""
File output component with rotation and compression support
"""

import json
import os
import gzip
import shutil
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from ..components import OutputComponent

class Output(OutputComponent):
    """File output component with rotation and compression"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.file_path = config.get("path")
        self.encoding = config.get("encoding", "utf-8")
        self.format = config.get("format", "json")  # json or text
        self.rotate = config.get("rotate", True)
        self.max_size = self._parse_size(config.get("max_size", "100M"))
        self.max_files = config.get("max_files", 10)
        self.compress = config.get("compress", True)
        self.compress_after = config.get("compress_after", 1)  # Compress after N rotations
        self._file = None
        self._current_size = 0
        
        if not self.file_path:
            raise ValueError("File path is required")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        
        # Initialize file handle
        self._open_file()
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string (e.g., '100M', '1G') to bytes"""
        units = {'B': 1, 'K': 1024, 'M': 1024**2, 'G': 1024**3}
        try:
            number = float(size_str[:-1])
            unit = size_str[-1].upper()
            return int(number * units[unit])
        except (ValueError, KeyError):
            return 10 * 1024 * 1024  # Default to 10MB
    
    def _open_file(self) -> None:
        """Open the output file"""
        try:
            self._file = open(self.file_path, "a", encoding=self.encoding)
            self._current_size = os.path.getsize(self.file_path)
        except Exception as e:
            self.logger.error(f"Error opening file: {e}")
            raise
    
    def write(self, data: Dict[str, Any]) -> None:
        """Write data to file with rotation and compression"""
        try:
            # Format the data
            if self.format == "json":
                output = json.dumps(data, default=str) + "\n"
            else:
                # Text format with timestamp
                timestamp = datetime.now().isoformat()
                output = f"[{timestamp}] {data.get('message', '')}\n"
            
            # Check if rotation is needed
            if self.rotate and self._current_size + len(output.encode(self.encoding)) > self.max_size:
                self._rotate_file()
            
            # Write to file
            self._file.write(output)
            self._file.flush()  # Ensure data is written to disk
            self._current_size += len(output.encode(self.encoding))
            
        except Exception as e:
            self.logger.error(f"Error writing to file: {e}")
            self._reopen_file()  # Try to reopen file on error
    
    def _reopen_file(self) -> None:
        """Reopen the file handle"""
        try:
            if self._file:
                self._file.close()
            self._open_file()
        except Exception as e:
            self.logger.error(f"Error reopening file: {e}")
    
    def _rotate_file(self) -> None:
        """Rotate log files with compression"""
        try:
            # Close current file
            if self._file:
                self._file.close()
                self._file = None
            
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
            
            # Compress old files if needed
            if self.compress:
                for i in range(1, self.max_files + 1):
                    if i > self.compress_after:
                        old_file = f"{self.file_path}.{i}"
                        if os.path.exists(old_file):
                            self._compress_file(old_file)
            
            # Open new file
            self._open_file()
            
        except Exception as e:
            self.logger.error(f"Error rotating log files: {e}")
            self._reopen_file()
    
    def _compress_file(self, file_path: str) -> None:
        """Compress a file using gzip"""
        try:
            with open(file_path, 'rb') as f_in:
                with gzip.open(f"{file_path}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(file_path)  # Remove original file after compression
        except Exception as e:
            self.logger.error(f"Error compressing file {file_path}: {e}")
    
    def close(self) -> None:
        """Cleanup resources"""
        try:
            if self._file:
                self._file.close()
                self._file = None
        except Exception as e:
            self.logger.error(f"Error closing file: {e}") 