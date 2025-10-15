"""In-memory input driver for testing and pipelines."""

from __future__ import annotations

import asyncio
from asyncio import QueueEmpty
from typing import Optional

from ..components.base import InputDriver


class MemoryInput(InputDriver):
    """Input driver backed by an :class:`asyncio.Queue`."""

    def __init__(self, config):
        super().__init__(config)
        self._queue: "asyncio.Queue[str]" = asyncio.Queue()
        messages = self.config.get("messages")
        if messages:
            for line in messages.splitlines():
                self._queue.put_nowait(line)
        self._closed = False
        self._idle_sleep = float(self.config.get("idle_sleep", 0.01))

    async def read(self) -> Optional[str]:
        if self._closed:
            return None
        try:
            return self._queue.get_nowait()
        except QueueEmpty:
            await asyncio.sleep(self._idle_sleep)
            return None

    async def stop(self) -> None:
        self._closed = True

    async def send(self, message: str) -> None:
        """Inject *message* into the input stream."""

        await self._queue.put(message)
