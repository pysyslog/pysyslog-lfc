"""
TCP output component with connection pooling and security features
"""

import json
import socket
import ssl
import threading
import time
from typing import Dict, Any, Optional, List
from queue import Queue
from dataclasses import dataclass
from ..components import OutputComponent

@dataclass
class Connection:
    """Represents a TCP connection"""
    socket: socket.socket
    last_used: float
    in_use: bool

class Output(OutputComponent):
    """TCP output component with connection pooling"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 514)
        self.format = config.get("format", "json")
        self.reconnect_delay = config.get("reconnect_delay", 5)
        self.max_retries = config.get("max_retries", 3)
        self.connection_timeout = config.get("connection_timeout", 10)
        self.keep_alive = config.get("keep_alive", True)
        self.ssl_enabled = config.get("ssl_enabled", False)
        self.ssl_verify = config.get("ssl_verify", True)
        self.ssl_cert = config.get("ssl_cert")
        self.ssl_key = config.get("ssl_key")
        self.ssl_ca = config.get("ssl_ca")
        self.max_connections = config.get("max_connections", 5)
        self.connections: List[Connection] = []
        self.queue = Queue()
        self.thread = None
        self.running = False
        self._lock = threading.Lock()
    
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
        """Sender thread loop with connection pooling"""
        while self.running:
            try:
                # Get data from queue
                data = self.queue.get(timeout=1)
                
                # Get or create connection
                conn = self._get_connection()
                if not conn:
                    self.logger.error("Failed to establish connection")
                    continue
                
                # Send data
                try:
                    conn.socket.sendall(data.encode())
                    conn.last_used = time.time()
                except socket.error as e:
                    self.logger.error(f"Socket error: {e}")
                    self._remove_connection(conn)
                    continue
                
            except Queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in sender loop: {e}")
    
    def _get_connection(self) -> Optional[Connection]:
        """Get an available connection or create a new one"""
        with self._lock:
            # Try to reuse existing connection
            for conn in self.connections:
                if not conn.in_use:
                    conn.in_use = True
                    return conn
            
            # Create new connection if under limit
            if len(self.connections) < self.max_connections:
                try:
                    sock = self._create_socket()
                    conn = Connection(socket=sock, last_used=time.time(), in_use=True)
                    self.connections.append(conn)
                    return conn
                except Exception as e:
                    self.logger.error(f"Error creating connection: {e}")
            
            return None
    
    def _create_socket(self) -> socket.socket:
        """Create a new socket with optional SSL"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.connection_timeout)
        
        if self.ssl_enabled:
            context = ssl.create_default_context()
            if not self.ssl_verify:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            if self.ssl_cert and self.ssl_key:
                context.load_cert_chain(self.ssl_cert, self.ssl_key)
            if self.ssl_ca:
                context.load_verify_locations(self.ssl_ca)
            sock = context.wrap_socket(sock, server_hostname=self.host)
        
        sock.connect((self.host, self.port))
        return sock
    
    def _remove_connection(self, conn: Connection) -> None:
        """Remove a failed connection"""
        with self._lock:
            try:
                conn.socket.close()
            except:
                pass
            if conn in self.connections:
                self.connections.remove(conn)
    
    def _cleanup_connections(self) -> None:
        """Clean up idle connections"""
        with self._lock:
            current_time = time.time()
            for conn in self.connections[:]:
                if not conn.in_use and (current_time - conn.last_used) > 300:  # 5 minutes
                    self._remove_connection(conn)
    
    def close(self) -> None:
        """Cleanup resources"""
        self.running = False
        if self.thread:
            self.thread.join()
        
        # Close all connections
        with self._lock:
            for conn in self.connections:
                try:
                    conn.socket.close()
                except:
                    pass
            self.connections.clear() 