"""Dummy http server

Responds to any request with the port of the server

if URL ends with /ws, a websocket connection is made
"""

import asyncio
import sys
from functools import partial
from http import HTTPStatus

import websockets


async def process_request(connection, request, port):
    if request.path.endswith("/ws"):
        return None
    headers = {
        "Content-Type": "text/plain",
        "Host": request.headers.get("Host", "None"),
        "Origin": request.headers.get("Origin", "None"),
    }
    return connection.respond(HTTPStatus.OK, headers, str(port).encode("utf8"))


async def send_port(websocket):
    _ip, port = websocket.local_address
    await websocket.send(str(port))


async def main(port, *, _start_future=None, _stop_future=None):
    # allow signaling a stop (in tests)
    if _stop_future is None:
        _stop_future = asyncio.Future()

    async with websockets.serve(
        send_port,
        host="127.0.0.1",
        port=port,
        process_request=partial(process_request, port=port),
    ):
        if _start_future:
            _start_future.set_result(None)
        # wait forever
        await _stop_future


if __name__ == "__main__":
    from sys import argv

    if len(argv) != 2:
        sys.exit("Please specify a port for the backend")
    port = int(argv[1])
    asyncio.run(main(port))
