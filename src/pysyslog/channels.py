"""Reliable in-memory queues used by flows to hand off work."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .config import ChannelConfig


@dataclass(slots=True)
class ChannelMessage:
    """Internal message container with retry metadata."""

    id: int
    payload: Any
    attempts: int = 0
    last_attempt: float = field(default_factory=lambda: 0.0)


class Channel:
    """A reliability queue backed by :class:`asyncio.Queue`."""

    def __init__(self, config: ChannelConfig, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.config = config
        self.loop = loop
        self._queue: "asyncio.Queue[ChannelMessage]" = asyncio.Queue(maxsize=config.maxsize)
        self._inflight: Dict[int, ChannelMessage] = {}
        self._counter = 0
        self._closed = False
        self._resender: Optional[asyncio.Task[None]] = None

    async def __aenter__(self) -> "Channel":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - exercised in runtime
        await self.close()

    async def start(self) -> None:
        if self._closed:
            self._closed = False
        if self.loop is None:
            self.loop = asyncio.get_running_loop()
        if self._resender is None or self._resender.done():
            self._resender = asyncio.create_task(self._monitor_ack_timeouts())

    async def put(self, payload: Any) -> None:
        if self._closed:
            raise RuntimeError("Channel is closed")
        message = ChannelMessage(id=self._next_id(), payload=payload)
        await self._queue.put(message)

    async def get(self) -> tuple[int, Any]:
        if self._closed:
            raise RuntimeError("Channel is closed")
        message = await self._queue.get()
        message.attempts += 1
        if self.loop is None:
            self.loop = asyncio.get_running_loop()
        message.last_attempt = self.loop.time()
        self._inflight[message.id] = message
        return message.id, message.payload

    async def ack(self, token: int) -> None:
        message = self._inflight.pop(token, None)
        if message is None:
            raise KeyError(f"Unknown delivery token {token}")

    async def nack(self, token: int, *, requeue: bool = True) -> None:
        message = self._inflight.pop(token, None)
        if message is None:
            raise KeyError(f"Unknown delivery token {token}")
        if not requeue:
            return
        if message.attempts >= self.config.retry_limit:
            return
        await self._queue.put(message)

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._resender:
            self._resender.cancel()
            try:
                await self._resender
            except asyncio.CancelledError:  # pragma: no cover - normal shutdown
                pass
            self._resender = None
        # Drain inflight without retries
        self._inflight.clear()
        while not self._queue.empty():
            self._queue.get_nowait()
            self._queue.task_done()

    def _next_id(self) -> int:
        self._counter += 1
        return self._counter

    async def _monitor_ack_timeouts(self) -> None:
        try:
            while not self._closed:
                await asyncio.sleep(self.config.ack_timeout / 2)
                if self._closed:
                    break
                now = self.loop.time()
                expired = [
                    message
                    for message in list(self._inflight.values())
                    if now - message.last_attempt >= self.config.ack_timeout
                ]
                for message in expired:
                    if message.attempts >= self.config.retry_limit:
                        self._inflight.pop(message.id, None)
                        continue
                    self._inflight.pop(message.id, None)
                    await self._queue.put(message)
        except asyncio.CancelledError:  # pragma: no cover - normal shutdown
            return


class ChannelRegistry:
    """Factory for :class:`Channel` instances."""

    def __init__(self, configs: Dict[str, ChannelConfig]):
        self._configs = configs
        self._channels: Dict[str, Channel] = {}

    def get(self, name: str) -> Channel:
        if name not in self._channels:
            if name not in self._configs:
                raise KeyError(f"Unknown channel {name!r}")
            self._channels[name] = Channel(self._configs[name])
        return self._channels[name]

    def all(self) -> Dict[str, Channel]:  # pragma: no cover - helper for runtime
        return dict(self._channels)
