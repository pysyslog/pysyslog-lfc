"""
File input component with built-in file watching
"""

import os
import time
import logging
from typing import Optional, Dict, Any
from threading import Thread, Event
from ..components import InputComponent

class FileWatcher(Thread):
    """File watcher thread using polling"""
    
    def __init__(self, file_path: str, callback, check_interval: float = 1.0):
        super().__init__()
        self.file_path = file_path
        self.callback = callback
        self.check_interval = check_interval
        self.stop_event = Event()
        self.last_size = 0
        self.last_mtime = 0
    
    def run(self) -> None:
        """Run the file watcher"""
        while not self.stop_event.is_set():
            try:
                if os.path.exists(self.file_path):
                    current_size = os.path.getsize(self.file_path)
                    current_mtime = os.path.getmtime(self.file_path)
                    
                    # Check if file has changed
                    if current_size != self.last_size or current_mtime != self.last_mtime:
                        self.callback()
                        self.last_size = current_size
                        self.last_mtime = current_mtime
                else:
                    # File doesn't exist, wait and check again
                    time.sleep(self.check_interval)
                    continue
                
                time.sleep(self.check_interval)
            except Exception as e:
                logging.error(f"Error watching file: {e}")
                time.sleep(self.check_interval)
    
    def stop(self) -> None:
        """Stop the file watcher"""
        self.stop_event.set()

class Input(InputComponent):
    """File input component"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.file_path = config.get("path")
        self.follow = config.get("follow", True)
        self.encoding = config.get("encoding", "utf-8")
        self.position = 0
        self.watcher = None
        self.check_interval = config.get("check_interval", 1.0)
        
        if not self.file_path:
            raise ValueError("File path is required")
        
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        if self.follow:
            self._setup_watcher()
    
    def _setup_watcher(self) -> None:
        """Setup file watcher"""
        try:
            self.watcher = FileWatcher(
                self.file_path,
                self._on_file_change,
                self.check_interval
            )
            self.watcher.daemon = True
            self.watcher.start()
            self.logger.info(f"Started watching {self.file_path}")
        except Exception as e:
            self.logger.error(f"Error setting up file watcher: {e}")
            self.follow = False
    
    def _on_file_change(self) -> None:
        """Handle file change events"""
        try:
            self.read()
        except Exception as e:
            self.logger.error(f"Error handling file change: {e}")
    
    def read(self) -> Optional[str]:
        """Read data from file"""
        try:
            # Check if file has been rotated
            if not os.path.exists(self.file_path):
                self.logger.warning(f"Log file {self.file_path} no longer exists")
                return None
            
            with open(self.file_path, "r", encoding=self.encoding) as f:
                f.seek(self.position)
                data = f.read()
                
                # Check if file was truncated
                if f.tell() < self.position:
                    self.logger.info(f"Log file {self.file_path} was truncated")
                    self.position = 0
                else:
                    self.position = f.tell()
                
                return data if data else None
        except Exception as e:
            self.logger.error(f"Error reading log file: {e}")
            return None
    
    def close(self) -> None:
        """Cleanup resources"""
        if self.watcher:
            try:
                self.watcher.stop()
                self.watcher.join()
            except Exception as e:
                self.logger.error(f"Error stopping file watcher: {e}") 