"""Output components for pysyslog."""

from .memory import MemoryOutput
from .stdout import StdoutOutput

__all__ = ["MemoryOutput", "StdoutOutput"]

