"""
Flow input component for chaining flows
"""

from typing import Optional, Dict, Any
from queue import Queue

from ..components import InputComponent

class Input(InputComponent):
    """Flow input component"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.flow_name = config.get("name")
        self.queue: Optional[Queue] = None
        
        if not self.flow_name:
            raise ValueError("Flow name is required")
    
    def set_queue(self, queue: Queue) -> None:
        """Set the input queue from the source flow"""
        self.queue = queue
    
    def read(self) -> Optional[str]:
        """Read data from the source flow's queue"""
        if not self.queue:
            self.logger.error("No source queue configured")
            return None
        
        try:
            return self.queue.get(timeout=1)
        except Exception as e:
            self.logger.error(f"Error reading from queue: {e}")
            return None
    
    def close(self) -> None:
        """Cleanup resources"""
        pass 