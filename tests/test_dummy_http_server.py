import asyncio
import sys

import pytest
import websockets

from .dummy_http_server import main


# quick test that the dummy http server for tests works!
@pytest.mark.skipif(sys.version_info < (3, 9), reason="websockets require Python 3.9")
async def test_dummy_server():
    port = 5678
    start_future = asyncio.Future()
    stop_future = asyncio.Future()
    req_url = f"ws://127.0.0.1:{port}/ws"
    main_future = asyncio.ensure_future(
        main(port, _start_future=start_future, _stop_future=stop_future)
    )
    await asyncio.wait(
        [start_future, main_future], timeout=5, return_when=asyncio.FIRST_COMPLETED
    )
    if main_future.done():
        main_future.result()
    async with websockets.connect(req_url) as websocket:
        ws_port = await websocket.recv()
    assert ws_port == str(port)
    stop_future.cancel()
    try:
        await main_future
    except asyncio.CancelledError:
        pass
