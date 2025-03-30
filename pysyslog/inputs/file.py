"""
File input component for reading log files across different Linux distributions.
Supports various log file locations and formats based on the distribution.
"""

import os
import logging
from typing import Optional, Dict, List
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
    """File input component for reading log files"""
    
    # Distribution-specific log paths
    LOG_PATHS = {
        'messages': {
            'rhel': '/var/log/messages',
            'centos': '/var/log/messages',
            'rocky': '/var/log/messages',
            'ubuntu': None,  # Ubuntu uses syslog
            'debian': None,  # Debian uses syslog
            'suse': '/var/log/messages',
            'opensuse': '/var/log/messages',
            'alpine': '/var/log/messages'
        },
        'syslog': {
            'rhel': None,  # RHEL uses messages
            'centos': None,  # CentOS uses messages
            'rocky': None,  # Rocky uses messages
            'ubuntu': '/var/log/syslog',
            'debian': '/var/log/syslog',
            'suse': None,  # SUSE uses messages
            'opensuse': None,  # OpenSUSE uses messages
            'alpine': '/var/log/syslog'
        },
        'secure': {
            'rhel': '/var/log/secure',
            'centos': '/var/log/secure',
            'rocky': '/var/log/secure',
            'ubuntu': '/var/log/auth.log',
            'debian': '/var/log/auth.log',
            'suse': '/var/log/secure',
            'opensuse': '/var/log/secure',
            'alpine': '/var/log/secure'
        }
    }
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.file_path = config.get("path")
        self.follow = config.get("follow", True)
        self.encoding = config.get("encoding", "utf-8")
        self.position = 0
        self.observer = None
        self._distribution = self._detect_distribution()
        
        if not self.file_path:
            self.file_path = self._get_default_log_path()
        
        if not self.file_path:
            raise ValueError("No valid log path found for this distribution")
        
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Log file not found: {self.file_path}")
        
        if self.follow:
            self._setup_observer()
    
    def _detect_distribution(self) -> str:
        """Detect the Linux distribution"""
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('ID='):
                        return line.split('=')[1].strip().lower().strip('"')
        except Exception:
            self.logger.warning("Could not detect distribution")
        return 'unknown'
    
    def _get_default_log_path(self) -> Optional[str]:
        """Get the default log path based on distribution and log type"""
        log_type = self.config.get("log_type", "messages")
        if log_type in self.LOG_PATHS:
            return self.LOG_PATHS[log_type].get(self._distribution)
        return None
    
    def _setup_observer(self) -> None:
        """Setup file system observer with error handling"""
        try:
            self.observer = Observer()
            handler = FileHandler(self._on_file_change)
            self.observer.schedule(handler, os.path.dirname(self.file_path), recursive=False)
            self.observer.start()
            self.logger.info(f"Started watching {self.file_path}")
        except Exception as e:
            self.logger.error(f"Error setting up file observer: {e}")
            self.follow = False  # Disable following if observer setup fails
    
    def _on_file_change(self) -> None:
        """Handle file change events with error handling"""
        try:
            self.read()
        except Exception as e:
            self.logger.error(f"Error handling file change: {e}")
    
    def read(self) -> Optional[str]:
        """Read data from file with error handling and rotation detection"""
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
        if self.observer:
            try:
                self.observer.stop()
                self.observer.join()
            except Exception as e:
                self.logger.error(f"Error stopping file observer: {e}") 