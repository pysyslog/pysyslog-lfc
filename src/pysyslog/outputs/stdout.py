"""Send rendered log entries to stdout or stderr."""

from __future__ import annotations

import asyncio
import sys
from typing import Any

from ..components.base import Output


class StdoutOutput(Output):
    """Write output to the configured standard stream."""

    def __init__(self, config):
        super().__init__(config)
        stream_name = self.config.get("stream", "stdout")
        if stream_name not in {"stdout", "stderr"}:
            raise ValueError("stream must be 'stdout' or 'stderr'")
        self._stream = getattr(sys, stream_name)
        self._append_newline = self.config.get("newline", "true").lower() in {"1", "true", "yes"}

    async def write(self, record: Any) -> None:
        text = record if isinstance(record, str) else str(record)
        if self._append_newline and not text.endswith("\n"):
            text = f"{text}\n"
        await asyncio.to_thread(self._stream.write, text)
        await asyncio.to_thread(self._stream.flush)
