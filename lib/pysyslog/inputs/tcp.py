"""
TCP input component
"""

import socket
import threading
from typing import Optional, List

from ..components import InputComponent

class Input(InputComponent):
    """TCP input component"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.host = config.get("host", "0.0.0.0")
        self.port = config.get("port", 514)
        self.max_connections = config.get("max_connections", 10)
        self.socket = None
        self.clients: List[socket.socket] = []
        self.running = False
        
        if not self.port:
            raise ValueError("Port is required")
    
    def setup(self) -> None:
        """Setup TCP socket"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(self.max_connections)
            self.logger.info(f"Listening on TCP {self.host}:{self.port}")
            
            self.running = True
            threading.Thread(target=self._accept_connections, daemon=True).start()
        except Exception as e:
            self.logger.error(f"Error setting up TCP socket: {e}")
            raise
    
    def _accept_connections(self) -> None:
        """Accept incoming connections"""
        while self.running:
            try:
                client, addr = self.socket.accept()
                self.clients.append(client)
                self.logger.info(f"New connection from {addr}")
                threading.Thread(target=self._handle_client, args=(client,), daemon=True).start()
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error accepting connection: {e}")
    
    def _handle_client(self, client: socket.socket) -> None:
        """Handle client connection"""
        try:
            while self.running:
                data = client.recv(4096)
                if not data:
                    break
                self._process_data(data.decode("utf-8"))
        except Exception as e:
            self.logger.error(f"Error handling client: {e}")
        finally:
            self.clients.remove(client)
            client.close()
    
    def _process_data(self, data: str) -> None:
        """Process received data"""
        # Override this method in subclasses to handle the data
        pass
    
    def read(self) -> Optional[str]:
        """Read data from TCP socket"""
        # This method is not used as we handle data in _handle_client
        return None
    
    def close(self) -> None:
        """Cleanup resources"""
        self.running = False
        if self.socket:
            self.socket.close()
        
        for client in self.clients:
            try:
                client.close()
            except:
                pass 