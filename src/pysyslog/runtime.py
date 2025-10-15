"""Runtime orchestration for pysyslog."""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Optional

from .channels import ChannelRegistry
from .config import ConfigLoader, RuntimeConfig
from .flow import Flow
from .components.registry import ComponentRegistry

logger = logging.getLogger(__name__)


class Runtime:
    """Create and manage flows based on a configuration."""

    def __init__(
        self,
        config: RuntimeConfig,
        *,
        registry: Optional[ComponentRegistry] = None,
    ) -> None:
        self.config = config
        self.registry = registry or ComponentRegistry()
        self.channel_registry = ChannelRegistry(config.channels)
        self.flows: Dict[str, Flow] = {
            flow_config.name: Flow(flow_config, self.registry, self.channel_registry)
            for flow_config in config.flows
        }

    async def start(self) -> None:
        logger.info("Starting %d flows", len(self.flows))
        for flow in self.flows.values():
            await flow.start()

    async def stop(self) -> None:
        for flow in self.flows.values():
            await flow.stop()
        for channel in self.channel_registry.all().values():
            await channel.close()

    async def run_forever(self) -> None:
        await self.start()
        stop_event = asyncio.Event()
        try:
            await stop_event.wait()
        except asyncio.CancelledError:  # pragma: no cover - normal shutdown
            raise
        finally:
            await self.stop()


async def run_from_file(path: str) -> None:
    loader = ConfigLoader()
    config = loader.load(path)
    runtime = Runtime(config)
    await runtime.run_forever()
