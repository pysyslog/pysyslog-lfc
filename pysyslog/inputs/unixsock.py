"""
Unix socket input component for receiving system logs
"""

import os
import socket
import logging
from typing import Optional
from ..components import InputComponent

class Input(InputComponent):
    """Unix socket input component for receiving system logs"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.socket_path = config.get('socket_path', '/dev/log')
        self.socket = None
        self.buffer_size = config.get('buffer_size', 65536)
        self.logger = logging.getLogger(__name__)
    
    def setup(self) -> None:
        """Setup the Unix socket"""
        try:
            # If the socket already exists, remove it
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
            
            # Create Unix domain socket
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            self.socket.bind(self.socket_path)
            
            # Set socket permissions to allow all users to write
            # 666 allows all users to read/write
            os.chmod(self.socket_path, 0o666)
            
            # Add socket to systemd-journal group if it exists
            try:
                import grp
                journal_group = grp.getgrnam('systemd-journal')
                os.chown(self.socket_path, -1, journal_group.gr_gid)
            except KeyError:
                self.logger.warning("systemd-journal group not found, using default permissions")
            
            self.logger.info(f"Unix socket created at {self.socket_path}")
        except Exception as e:
            self.logger.error(f"Error setting up Unix socket: {e}")
            raise
    
    def read(self) -> Optional[str]:
        """Read data from the Unix socket"""
        try:
            data, _ = self.socket.recvfrom(self.buffer_size)
            return data.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Error reading from Unix socket: {e}")
            return None
    
    def close(self) -> None:
        """Cleanup the Unix socket"""
        if self.socket:
            try:
                self.socket.close()
                if os.path.exists(self.socket_path):
                    os.unlink(self.socket_path)
            except Exception as e:
                self.logger.error(f"Error closing Unix socket: {e}") 