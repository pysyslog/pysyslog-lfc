"""Output that stores records in memory (used for testing)."""

from __future__ import annotations

from typing import Any, List

from ..components.base import Output


class MemoryOutput(Output):
    """Collect records in :attr:`records`."""

    def __init__(self, config):
        super().__init__(config)
        self.records: List[Any] = []

    async def write(self, record: Any) -> None:
        self.records.append(record)
