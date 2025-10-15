from __future__ import annotations

import asyncio

from pysyslog.channels import ChannelRegistry
from pysyslog.components.registry import ComponentRegistry
from pysyslog.config import ConfigLoader
from pysyslog.flow import Flow
from pysyslog.outputs.memory import MemoryOutput


def test_flow_processes_messages_with_filters():
    text = """
[flow.demo]
input.type = memory
parser.type = json
output.type = memory
output.format = text
format.template = {message}
filter.allow.type = field
filter.allow.field = level
filter.allow.op = eq
filter.allow.value = info
filter.allow.stage = parser
"""
    config = ConfigLoader().loads(text)
    registry = ComponentRegistry()
    channel_registry = ChannelRegistry(config.channels)
    flow = Flow(config.get_flow("demo"), registry, channel_registry)

    async def scenario():
        await flow.start()
        try:
            memory_input = flow._input  # type: ignore[attr-defined]
            memory_output = flow._output  # type: ignore[attr-defined]
            await memory_input.send('{"message": "accepted", "level": "info"}')
            await memory_input.send('{"message": "ignored", "level": "debug"}')
            await asyncio.sleep(0.1)
            assert memory_output.records == ["accepted"]
        finally:
            await flow.stop()

    asyncio.run(scenario())


class FlakyMemoryOutput(MemoryOutput):
    def __init__(self, config):
        super().__init__(config)
        self._failed = False

    async def write(self, record):
        if not self._failed:
            self._failed = True
            raise RuntimeError("simulated failure")
        await super().write(record)


def test_flow_retries_on_output_failure():
    text = """
[flow.retry]
input.type = memory
parser.type = json
output.type = flaky
output.format = text
format.template = {message}
"""
    config = ConfigLoader().loads(text)
    registry = ComponentRegistry()
    registry.register_output("flaky", FlakyMemoryOutput)
    channel_registry = ChannelRegistry(config.channels)
    flow = Flow(config.get_flow("retry"), registry, channel_registry)

    async def scenario():
        await flow.start()
        try:
            memory_input = flow._input  # type: ignore[attr-defined]
            flaky_output = flow._output  # type: ignore[attr-defined]
            await memory_input.send('{"message": "retry", "level": "info"}')
            await asyncio.sleep(0.2)
            assert flaky_output.records == ["retry"]
        finally:
            await flow.stop()

    asyncio.run(scenario())
