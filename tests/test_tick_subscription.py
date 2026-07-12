import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pocketoptionapi_async import AsyncPocketOptionClient
from pocketoptionapi_async.models import ConnectionStatus


@pytest.mark.asyncio
async def test_subscribe_ticks_sends_change_symbol_and_waits_for_tick():
    ssid = r'42["auth",{"session":"test","isDemo":1,"uid":1,"platform":1}]'
    client = AsyncPocketOptionClient(ssid=ssid, is_demo=True, enable_logging=False)
    client._websocket.websocket = MagicMock()
    client._websocket.websocket.closed = False
    client._websocket.connection_info = MagicMock(status=ConnectionStatus.CONNECTED)
    client._websocket.send_message = AsyncMock()

    async def publish_tick():
        await asyncio.sleep(0.01)
        await client._on_stream_update([["USDJPY_otc", 1_700_000_000.1, 150.25]])

    publisher = asyncio.create_task(publish_tick())
    tick = await client.subscribe_ticks("USDJPY_otc", wait_timeout=0.5)
    await publisher

    client._websocket.send_message.assert_awaited_once_with(
        '42["changeSymbol", {"asset": "USDJPY_otc", "period": 60}]'
    )
    assert tick is not None
    assert tick["asset"] == "USDJPY_otc"
    assert tick["price"] == 150.25
