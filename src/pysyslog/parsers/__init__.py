"""Parser components for pysyslog."""

from .json import JsonParser
from .text import TextParser

__all__ = ["JsonParser", "TextParser"]

