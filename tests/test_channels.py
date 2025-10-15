from __future__ import annotations

import asyncio

from pysyslog.channels import Channel, ChannelConfig


def test_channel_ack_and_nack_retry():
    async def scenario():
        channel = Channel(ChannelConfig(name="test", maxsize=4, ack_timeout=0.05, retry_limit=3))
        await channel.start()
        await channel.put("hello")

        token, payload = await channel.get()
        assert payload == "hello"

        # Nack and ensure the message is re-delivered
        await channel.nack(token)
        token2, payload2 = await channel.get()
        assert payload2 == "hello"
        assert token2 == token

        await channel.ack(token2)
        await channel.close()

    asyncio.run(scenario())


def test_channel_ack_timeout_requeues():
    async def scenario():
        channel = Channel(ChannelConfig(name="test", maxsize=4, ack_timeout=0.05, retry_limit=2))
        await channel.start()
        await channel.put("delayed")
        token, payload = await channel.get()
        assert payload == "delayed"

        await asyncio.sleep(0.1)
        token2, payload2 = await channel.get()
        assert payload2 == "delayed"
        assert token2 == token
        await channel.ack(token2)
        await channel.close()

    asyncio.run(scenario())
