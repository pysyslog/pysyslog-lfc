"""
Memory output component for flow chaining
"""

from typing import Dict, Any
from queue import Queue

from ..components import OutputComponent

class Output(OutputComponent):
    """Memory output component"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.queue = Queue()
    
    def write(self, data: Dict[str, Any]) -> None:
        """Write data to memory queue"""
        try:
            self.queue.put(data)
        except Exception as e:
            self.logger.error(f"Error writing to queue: {e}")
    
    def get_queue(self) -> Queue:
        """Get the output queue"""
        return self.queue
    
    def close(self) -> None:
        """Cleanup resources"""
        pass 