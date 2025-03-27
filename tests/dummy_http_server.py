"""Dummy http server

Responds to any request with the port of the server

if URL ends with /ws, a websocket connection is made
"""

import asyncio
import sys
from functools import partial
from http import HTTPStatus

import websockets
from packaging.version import parse as V

_old_ws = V(websockets.__version__) < V("14")


# websockets 14 changed APIs
# drop _old_ws logic when we drop Python 3.8
# _old_ws signature: (path, request_headers, port)
async def process_request(connection, request, port):
    if _old_ws:
        path = connection
        request_headers = request
    else:
        path = request.path
        request_headers = request.headers

    if path.endswith("/ws"):
        return None

    headers = {
        "Content-Type": "text/plain",
        "Host": request_headers.get("Host", "None"),
        "Origin": request_headers.get("Origin", "None"),
    }

    if _old_ws:
        return (HTTPStatus.OK, headers, str(port).encode())
    else:
        response = connection.respond(HTTPStatus.OK, str(port))
        response.headers.update(headers)
        return response


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
