"""
Unix socket input component for receiving system logs across different Linux distributions.
Supports various syslog socket locations and permissions based on the distribution.
"""

import os
import socket
import logging
import platform
from typing import Optional, Dict
from ..components import InputComponent

class Input(InputComponent):
    """Unix socket input component for receiving system logs"""
    
    # Distribution-specific socket paths
    SOCKET_PATHS = {
        'rhel': '/dev/log',
        'centos': '/dev/log',
        'rocky': '/dev/log',
        'ubuntu': '/var/run/syslog',
        'debian': '/var/run/syslog',
        'suse': '/dev/log',
        'opensuse': '/dev/log',
        'alpine': '/dev/log'
    }
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.socket_path = config.get('socket_path', self._get_default_socket_path())
        self.socket = None
        self.buffer_size = config.get('buffer_size', 65536)
        self.logger = logging.getLogger(__name__)
        self._distribution = self._detect_distribution()
    
    def _detect_distribution(self) -> str:
        """Detect the Linux distribution"""
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('ID='):
                        return line.split('=')[1].strip().lower().strip('"')
        except Exception:
            self.logger.warning("Could not detect distribution, using default socket path")
        return 'unknown'
    
    def _get_default_socket_path(self) -> str:
        """Get the default socket path based on distribution"""
        return self.SOCKET_PATHS.get(self._distribution, '/dev/log')
    
    def setup(self) -> None:
        """Set up the Unix socket connection"""
        try:
            # Check if socket exists and is accessible
            if not os.path.exists(self.socket_path):
                self.logger.error(f"Socket path does not exist: {self.socket_path}")
                raise RuntimeError(f"Socket path does not exist: {self.socket_path}")
            
            # Check socket permissions
            socket_mode = os.stat(self.socket_path).st_mode
            if not socket.S_ISSOCK(socket_mode):
                self.logger.error(f"Path is not a socket: {self.socket_path}")
                raise RuntimeError(f"Path is not a socket: {self.socket_path}")
            
            # Create Unix domain socket
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            
            # Set socket options
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.buffer_size)
            
            # Connect to the socket
            self.socket.connect(self.socket_path)
            self.logger.info(f"Connected to Unix socket: {self.socket_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to set up Unix socket: {str(e)}")
            raise
    
    def read(self) -> Optional[str]:
        """Read data from the Unix socket"""
        try:
            if not self.socket:
                self.logger.error("Socket not initialized")
                return None
            
            data, _ = self.socket.recvfrom(self.buffer_size)
            return data.decode('utf-8', errors='replace')
            
        except Exception as e:
            self.logger.error(f"Error reading from Unix socket: {str(e)}")
            return None
    
    def close(self) -> None:
        """Close the Unix socket connection"""
        try:
            if self.socket:
                self.socket.close()
                self.socket = None
                self.logger.info("Closed Unix socket connection")
        except Exception as e:
            self.logger.error(f"Error closing Unix socket: {str(e)}") 