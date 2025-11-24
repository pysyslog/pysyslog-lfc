#!/usr/bin/env python3
"""Test script to verify the example configuration works with existing components."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pysyslog.channels import ChannelRegistry
from pysyslog.components.registry import ComponentRegistry
from pysyslog.config import ConfigLoader
from pysyslog.flow import Flow
from pysyslog.inputs.memory import MemoryInput
from pysyslog.outputs.memory import MemoryOutput


async def test_demo_flow():
    """Test the demo flow from the example configuration."""
    print("Testing demo flow...")
    
    config_text = """
[flow.demo]
input.type = memory
parser.type = json
output.type = memory
output.format = json
"""
    
    loader = ConfigLoader()
    config = loader.loads(config_text)
    registry = ComponentRegistry()
    channel_registry = ChannelRegistry(config.channels)
    flow = Flow(config.get_flow("demo"), registry, channel_registry)
    
    await flow.start()
    try:
        memory_input = flow._input  # type: ignore[attr-defined]
        memory_output = flow._output  # type: ignore[attr-defined]
        
        # Send test messages
        await memory_input.send('{"message": "test1", "level": "info"}')
        await memory_input.send('{"message": "test2", "level": "debug"}')
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Verify output
        assert len(memory_output.records) == 2, f"Expected 2 records, got {len(memory_output.records)}"
        print(f"✓ Demo flow processed {len(memory_output.records)} messages")
        print(f"  Records: {memory_output.records}")
    finally:
        await flow.stop()


async def test_filtered_flow():
    """Test the filtered flow from the example configuration."""
    print("\nTesting filtered flow...")
    
    config_text = """
[flow.filtered]
input.type = memory
parser.type = text
filter.info.type = field
filter.info.field = message
filter.info.op = contains
filter.info.value = ERROR
filter.info.stage = parser
output.type = memory
output.format = text
format.template = ERROR: {message}
"""
    
    loader = ConfigLoader()
    config = loader.loads(config_text)
    registry = ComponentRegistry()
    channel_registry = ChannelRegistry(config.channels)
    flow = Flow(config.get_flow("filtered"), registry, channel_registry)
    
    await flow.start()
    try:
        memory_input = flow._input  # type: ignore[attr-defined]
        memory_output = flow._output  # type: ignore[attr-defined]
        
        # Send test messages
        await memory_input.send("This is an ERROR message")
        await memory_input.send("This is a normal message")
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Verify output (only ERROR message should pass filter)
        assert len(memory_output.records) == 1, f"Expected 1 record, got {len(memory_output.records)}"
        assert "ERROR" in memory_output.records[0], "Filtered message should contain ERROR"
        print(f"✓ Filtered flow processed {len(memory_output.records)} message(s)")
        print(f"  Records: {memory_output.records}")
    finally:
        await flow.stop()


async def test_reliable_flow():
    """Test the reliable flow with channel from the example configuration."""
    print("\nTesting reliable flow with channel...")
    
    config_text = """
[flow.reliable]
input.type = memory
parser.type = json
output.type = memory
output.format = json
channel = reliable_queue

[channel.reliable_queue]
maxsize = 1000
ack_timeout = 30.0
retry_limit = 3
"""
    
    loader = ConfigLoader()
    config = loader.loads(config_text)
    registry = ComponentRegistry()
    channel_registry = ChannelRegistry(config.channels)
    flow = Flow(config.get_flow("reliable"), registry, channel_registry)
    
    await flow.start()
    try:
        memory_input = flow._input  # type: ignore[attr-defined]
        memory_output = flow._output  # type: ignore[attr-defined]
        
        # Send test messages
        await memory_input.send('{"message": "reliable1", "level": "info"}')
        await memory_input.send('{"message": "reliable2", "level": "warn"}')
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Verify output
        assert len(memory_output.records) == 2, f"Expected 2 records, got {len(memory_output.records)}"
        print(f"✓ Reliable flow processed {len(memory_output.records)} messages")
        print(f"  Records: {memory_output.records}")
    finally:
        await flow.stop()


async def main():
    """Run all tests."""
    try:
        await test_demo_flow()
        await test_filtered_flow()
        await test_reliable_flow()
        print("\n✓ All tests passed!")
        return 0
    except Exception as e:
        print(f"\n✗ Test failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

