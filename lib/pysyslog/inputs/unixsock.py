"""
Unix socket input component
"""

import socket
import os
from typing import Optional

from ..components import InputComponent

class Input(InputComponent):
    """Unix socket input component"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.socket_path = config.get("path", "/dev/log")
        self.sock = None
        self._setup_socket()
    
    def _setup_socket(self) -> None:
        """Setup Unix domain socket"""
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)
        
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.sock.bind(self.socket_path)
        os.chmod(self.socket_path, 0o666)  # Allow all users to write
    
    def read(self) -> Optional[str]:
        """Read data from socket"""
        try:
            data, _ = self.sock.recvfrom(65536)
            return data.decode("utf-8")
        except Exception as e:
            self.logger.error(f"Error reading from socket: {e}")
            return None
    
    def close(self) -> None:
        """Cleanup socket"""
        if self.sock:
            self.sock.close()
            if os.path.exists(self.socket_path):
                os.remove(self.socket_path) 