import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
import numpy as np
import sys
import websockets


class DummyServer(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Host", self.headers["Host"])
        self.send_header("Origin", self.headers["Origin"])
        self.end_headers()

    def generate(self, number_of_bytes):
        return np.random.bytes(number_of_bytes)

    def do_GET(self):
        self._set_headers()
        data = None
        if self.headers["RequestSize"] == "large":
            data = self.generate(10000000)  # 10MB
        else:
            data = self.generate(1)  # 1B
        self.wfile.write(data)


def run(port=9000):
    dummy_server = HTTPServer(("localhost", port), DummyServer)

    try:
        dummy_server.serve_forever()
    except KeyboardInterrupt:
        pass

    dummy_server.server_close()


if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
