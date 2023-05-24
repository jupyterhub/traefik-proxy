"""Dummy http server

Responds to any request with the port of the server

if URL ends with /ws, a websocket connection is made
"""

import asyncio
import sys
from functools import partial
from http import HTTPStatus

import websockets

from .conftest import Config


async def process_request(path, request_headers, port):
    if path.endswith("/ws"):
        return None
    headers = {
        "Content-Type": "text/plain",
        "Host": request_headers.get("Host", "None"),
        "Origin": request_headers.get("Origin", "None"),
    }
    return (HTTPStatus.OK, headers, str(port).encode("utf8"))


async def send_port(websocket, path):
    await websocket.send(str(websocket.port))


async def main(port):
    async with websockets.serve(
        send_port,
        host=Config.localhost,
        port=port,
        process_request=partial(process_request, port=port),
    ):
        # wait forever
        await asyncio.Future()


if __name__ == "__main__":
    from sys import argv

    if len(argv) != 2:
        sys.exit("Please specify a port for the backend")
    port = int(argv[1])
    asyncio.run(main(port))
