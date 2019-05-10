import asyncio
import websockets


async def send_port(websocket, path):
    print("sending hello")
    await websocket.send("Hi")
    await websocket.wait_closed()


if __name__ == "__main__":
    from sys import argv

    asyncio.get_event_loop().run_until_complete(
        websockets.serve(send_port, "localhost", 9000)
    )
    asyncio.get_event_loop().run_forever()
