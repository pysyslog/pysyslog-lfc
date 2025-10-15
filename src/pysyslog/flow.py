"""Asynchronous flow runner."""

from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Mapping, Optional

from .channels import Channel, ChannelRegistry
from .config import ChannelConfig, FlowConfig
from .components.registry import ComponentRegistry


class Flow:
    """A running pipeline that processes messages through a channel."""

    def __init__(
        self,
        config: FlowConfig,
        registry: ComponentRegistry,
        channel_registry: Optional[ChannelRegistry] = None,
    ) -> None:
        self.config = config
        self.registry = registry
        self.channel_registry = channel_registry or ChannelRegistry({})
        self.name = config.name

        self._input = registry.create_input(config.input.type, config.input.options)
        self._parser = registry.create_parser(config.parser.type, config.parser.options)
        self._output = registry.create_output(config.output.type, config.output.options)
        self._format = (
            registry.create_format(config.output_format, config.format_options)
            if config.output_format
            else None
        )
        self._filters: Dict[str, List] = {"input": [], "parser": [], "output": []}
        for filter_config in config.filters:
            filter_instance = registry.create_filter(
                filter_config.component.type, filter_config.component.options
            )
            filter_instance.stage = filter_config.stage
            self._filters.setdefault(filter_config.stage, []).append(filter_instance)

        self._channel_owner = False
        if config.channel:
            self._channel = self.channel_registry.get(config.channel)
        else:
            self._channel_owner = True
            self._channel = Channel(ChannelConfig(name=f"flow-{self.name}"))

        self._tasks: List[asyncio.Task[None]] = []
        self._stack: Optional[AsyncExitStack] = None
        self._running = False
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._stop_event.clear()

        self._stack = AsyncExitStack()
        await self._stack.__aenter__()
        await self._stack.enter_async_context(self._input)
        await self._stack.enter_async_context(self._parser)
        await self._stack.enter_async_context(self._output)
        if self._format:
            await self._stack.enter_async_context(self._format)
        for stage_filters in self._filters.values():
            for filt in stage_filters:
                await self._stack.enter_async_context(filt)
        if self._channel_owner:
            await self._stack.enter_async_context(self._channel)
        else:
            await self._channel.start()

        self._tasks = [
            asyncio.create_task(self._ingest_loop(), name=f"flow-{self.name}-ingest"),
            asyncio.create_task(self._drain_loop(), name=f"flow-{self.name}-drain"),
        ]

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        self._stop_event.set()
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:  # pragma: no cover - shutdown path
                pass
        self._tasks.clear()
        if self._stack is not None:
            await self._stack.__aexit__(None, None, None)
            self._stack = None

    async def _ingest_loop(self) -> None:
        try:
            while not self._stop_event.is_set():
                raw = await self._input.read()
                if raw is None:
                    await asyncio.sleep(0)
                    continue
                if not await self._apply_filters("input", {"raw": raw}):
                    continue
                parsed = await self._parser.parse(raw)
                if parsed is None:
                    continue
                if not await self._apply_filters("parser", parsed):
                    continue
                payload = parsed
                rendered = await self._format.format(parsed) if self._format else parsed
                await self._channel.put({"record": payload, "rendered": rendered})
        except asyncio.CancelledError:  # pragma: no cover - cooperative cancellation
            return

    async def _drain_loop(self) -> None:
        try:
            while not self._stop_event.is_set():
                token, payload = await self._channel.get()
                record = payload["record"]
                if not await self._apply_filters("output", record):
                    await self._channel.ack(token)
                    continue
                try:
                    await self._output.write(payload["rendered"])
                except Exception:  # pragma: no cover - defensive
                    await self._channel.nack(token)
                    await asyncio.sleep(0)
                else:
                    await self._channel.ack(token)
        except asyncio.CancelledError:  # pragma: no cover - cooperative cancellation
            return

    async def _apply_filters(self, stage: str, record: Mapping[str, Any]) -> bool:
        for filt in self._filters.get(stage, []):
            if not await filt.allow(record):
                return False
        return True
