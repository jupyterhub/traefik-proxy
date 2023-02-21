from http.server import BaseHTTPRequestHandler, HTTPServer
import asyncio
import websockets


class DummyServer(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Host", self.headers["Host"])
        self.send_header("Origin", self.headers["Origin"])
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        self.wfile.write(bytes(str(self.server.server_port), "utf-8"))


async def send_port(websocket, path):
    await websocket.send(str(websocket.port))


def run(port=80):
    dummy_server = HTTPServer(("127.0.0.1", port), DummyServer)

    try:
        dummy_server.serve_forever()
    except KeyboardInterrupt:
        pass

    dummy_server.server_close()


if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    elif len(argv) == 3:
        proto = str(argv[2])
        if proto == "http":
            run(port=int(argv[1]))
        elif proto == "ws":
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                # localhost can resolve to ::1. This causes issues on
                # docker, which disables the IPv6 stack by default,
                # resulting in the error 'Cannot assign requested address'.
                websockets.serve(send_port, "127.0.0.1", int(argv[1]))
            )
            loop.run_forever()
        else:
            raise ValueError(
                f"I know how to run 'http' or 'ws' servers, not {proto} servers"
            )
    else:
        run()
