"""
TCP output component
"""

import json
import socket
from typing import Dict, Any
from queue import Queue
import threading

from ..components import OutputComponent

class Output(OutputComponent):
    """TCP output component"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 514)
        self.format = config.get("format", "json")
        self.reconnect_delay = config.get("reconnect_delay", 5)
        self.socket = None
        self.connected = False
        self.queue = Queue()
        self.thread = None
        self.running = False
    
    def write(self, data: Dict[str, Any]) -> None:
        """Queue data for sending"""
        try:
            # Format data
            if self.format == "json":
                line = json.dumps(data) + "\n"
            else:
                line = str(data) + "\n"
            
            self.queue.put(line)
            
            # Start sender thread if not running
            if not self.running:
                self._start_sender()
        except Exception as e:
            self.logger.error(f"Error queueing data: {e}")
    
    def _start_sender(self) -> None:
        """Start the sender thread"""
        self.running = True
        self.thread = threading.Thread(target=self._sender_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def _sender_loop(self) -> None:
        """Sender thread loop"""
        while self.running:
            try:
                if not self.connected:
                    self._connect()
                
                # Get data from queue
                data = self.queue.get(timeout=1)
                
                # Send data
                self.socket.sendall(data.encode())
            except socket.error as e:
                self.logger.error(f"Socket error: {e}")
                self.connected = False
                self._reconnect()
            except Exception as e:
                self.logger.error(f"Error in sender loop: {e}")
    
    def _connect(self) -> None:
        """Connect to remote host"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.logger.info(f"Connected to {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            self.connected = False
    
    def _reconnect(self) -> None:
        """Attempt to reconnect"""
        import time
        time.sleep(self.reconnect_delay)
        self._connect()
    
    def close(self) -> None:
        """Cleanup resources"""
        self.running = False
        if self.thread:
            self.thread.join()
        if self.socket:
            self.socket.close() 