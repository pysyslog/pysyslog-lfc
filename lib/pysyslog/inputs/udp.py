"""
UDP input component
"""

import socket
from typing import Optional

from ..components import InputComponent

class Input(InputComponent):
    """UDP input component"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.host = config.get("host", "0.0.0.0")
        self.port = config.get("port", 514)
        self.buffer_size = config.get("buffer_size", 65535)
        self.socket = None
        
        if not self.port:
            raise ValueError("Port is required")
    
    def setup(self) -> None:
        """Setup UDP socket"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((self.host, self.port))
            self.logger.info(f"Listening on UDP {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Error setting up UDP socket: {e}")
            raise
    
    def read(self) -> Optional[str]:
        """Read data from UDP socket"""
        try:
            data, addr = self.socket.recvfrom(self.buffer_size)
            return data.decode("utf-8")
        except Exception as e:
            self.logger.error(f"Error reading from UDP socket: {e}")
            return None
    
    def close(self) -> None:
        """Cleanup resources"""
        if self.socket:
            self.socket.close() 