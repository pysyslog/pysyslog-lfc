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
        """Setup the Unix socket with proper permissions"""
        try:
            # If the socket already exists, remove it
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
            
            # Create Unix domain socket
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            self.socket.bind(self.socket_path)
            
            # Set secure permissions based on distribution
            if self._distribution in ['ubuntu', 'debian']:
                # Debian/Ubuntu typically use systemd-journal group
                os.chmod(self.socket_path, 0o660)
                try:
                    import grp
                    journal_group = grp.getgrnam('systemd-journal')
                    os.chown(self.socket_path, -1, journal_group.gr_gid)
                except KeyError:
                    self.logger.warning("systemd-journal group not found")
            else:
                # Other distributions typically allow all users to write
                os.chmod(self.socket_path, 0o666)
            
            self.logger.info(f"Unix socket created at {self.socket_path} with {oct(os.stat(self.socket_path).st_mode)[-3:]} permissions")
        except Exception as e:
            self.logger.error(f"Error setting up Unix socket: {e}")
            raise
    
    def read(self) -> Optional[str]:
        """Read data from the Unix socket with timeout"""
        try:
            # Set a timeout to prevent blocking indefinitely
            self.socket.settimeout(1.0)
            data, _ = self.socket.recvfrom(self.buffer_size)
            return data.decode('utf-8')
        except socket.timeout:
            return None
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