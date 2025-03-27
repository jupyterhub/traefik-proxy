import asyncio

import websockets
from tornado.httpclient import AsyncHTTPClient

from .dummy_http_server import main


# quick test that the dummy http server for tests works!
async def test_dummy_server(request):
    port = 5678
    start_future = asyncio.Future()
    stop_future = asyncio.Future()
    # stat dummy server, wait for it to start
    main_future = asyncio.ensure_future(
        main(port, _start_future=start_future, _stop_future=stop_future)
    )
    await asyncio.wait(
        [start_future, main_future], timeout=5, return_when=asyncio.FIRST_COMPLETED
    )
    if main_future.done():
        main_future.result()

    try:
        http_url = f"http://127.0.0.1:{port}/test"
        ws_url = f"ws://127.0.0.1:{port}/ws"
        resp = await AsyncHTTPClient().fetch(http_url)
        assert resp.body == str(port).encode()

        ws_url = f"ws://127.0.0.1:{port}/ws"

        async with websockets.connect(ws_url) as websocket:
            ws_port = await websocket.recv()
        assert ws_port == str(port)
    finally:
        stop_future.cancel()
        try:
            await main_future
        except asyncio.CancelledError:
            pass
