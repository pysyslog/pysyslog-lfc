"""Abstract component definitions."""

from __future__ import annotations

import abc
from contextlib import AbstractAsyncContextManager
from typing import Any, Mapping, Optional


class AsyncComponent(AbstractAsyncContextManager, metaclass=abc.ABCMeta):
    """Base class for all asynchronous components."""

    def __init__(self, config: Mapping[str, Any]):
        self.config = dict(config)

    async def __aenter__(self):  # pragma: no cover - trivial wrapper
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):  # pragma: no cover - trivial wrapper
        await self.stop()

    async def start(self) -> None:
        """Hook executed before the component is used."""

    async def stop(self) -> None:
        """Hook executed when the component is no longer used."""


class InputDriver(AsyncComponent):
    """A source of raw log events."""

    @abc.abstractmethod
    async def read(self) -> Optional[str]:
        """Return the next raw log line or ``None`` if no data is available."""


class Parser(AsyncComponent):
    """Convert raw input into structured dictionaries."""

    @abc.abstractmethod
    async def parse(self, message: str) -> Optional[Mapping[str, Any]]:
        """Parse *message* returning a dictionary or ``None`` to drop it."""


class Filter(AsyncComponent):
    """Filter structured log entries."""

    stage: str = "parser"

    @abc.abstractmethod
    async def allow(self, record: Mapping[str, Any]) -> bool:
        """Return ``True`` if the record should continue through the pipeline."""


class Output(AsyncComponent):
    """Sink for structured log records."""

    @abc.abstractmethod
    async def write(self, record: Mapping[str, Any]) -> None:
        """Write the given record."""


class OutputFormat(AsyncComponent):
    """Reusable formatting logic for outputs."""

    async def format(self, record: Mapping[str, Any]) -> Any:
        return record
