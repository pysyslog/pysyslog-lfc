"""
File input component
"""

import os
import time
from typing import Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..components import InputComponent

class FileHandler(FileSystemEventHandler):
    """Handler for file system events"""
    
    def __init__(self, callback):
        self.callback = callback
    
    def on_modified(self, event):
        if not event.is_directory:
            self.callback()

class Input(InputComponent):
    """File input component"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.file_path = config.get("path")
        self.follow = config.get("follow", True)
        self.encoding = config.get("encoding", "utf-8")
        self.position = 0
        self.observer = None
        
        if not self.file_path:
            raise ValueError("File path is required")
        
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        if self.follow:
            self._setup_observer()
    
    def _setup_observer(self) -> None:
        """Setup file system observer"""
        self.observer = Observer()
        handler = FileHandler(self._on_file_change)
        self.observer.schedule(handler, os.path.dirname(self.file_path), recursive=False)
        self.observer.start()
    
    def _on_file_change(self) -> None:
        """Handle file change events"""
        self.read()
    
    def read(self) -> Optional[str]:
        """Read data from file"""
        try:
            with open(self.file_path, "r", encoding=self.encoding) as f:
                f.seek(self.position)
                data = f.read()
                self.position = f.tell()
                return data if data else None
        except Exception as e:
            self.logger.error(f"Error reading file: {e}")
            return None
    
    def close(self) -> None:
        """Cleanup resources"""
        if self.observer:
            self.observer.stop()
            self.observer.join() 