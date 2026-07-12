import pytest

from pocketoptionapi_async import AsyncPocketOptionClient


@pytest.mark.asyncio
async def test_socketio_open_and_close_events_update_order_status():
    ssid = r'42["auth",{"session":"test","isDemo":1,"uid":1,"platform":1}]'
    client = AsyncPocketOptionClient(ssid=ssid, is_demo=True, enable_logging=False)
    client.refresh_balance = _no_balance_refresh

    request_id = "request-123"
    server_id = "deal-456"
    await client._on_order_opened(
        {
            "requestId": request_id,
            "id": server_id,
            "asset": "EURUSD_otc",
            "amount": 10,
            "command": 0,
            "time": 60,
        }
    )

    assert request_id in client._active_orders
    assert client._server_id_to_request_id[server_id] == request_id

    # successcloseOrder can contain the deal directly (without a deals list).
    await client._on_order_closed({"id": server_id, "profit": 8.5, "payout": 85})

    assert request_id not in client._active_orders
    assert request_id in client._order_results
    status = await client.check_win(request_id, max_wait_time=0.1)
    assert status["completed"] is True
    assert status["result"] == "win"


async def _no_balance_refresh():
    return None
