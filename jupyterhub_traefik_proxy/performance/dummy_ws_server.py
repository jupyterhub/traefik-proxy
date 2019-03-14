from http.server import BaseHTTPRequestHandler, HTTPServer
import asyncio
import websockets


def health_check(path, request_headers):
    if path == "/some_routespec/":
        print(request_headers)


async def send_port(websocket, path):
    print("sending hello")
    await websocket.send("Hi")
    await websocket.wait_closed()


if __name__ == "__main__":
    from sys import argv

    asyncio.get_event_loop().run_until_complete(
        websockets.serve(send_port, "localhost", 9000, process_request=health_check)
    )
    asyncio.get_event_loop().run_forever()
