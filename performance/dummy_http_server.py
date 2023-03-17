from secrets import token_hex

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route, WebSocketRoute

messages = {
    "small": "",
    "large": token_hex(500_000),  # 1MiB
}

ws_chunk_size = 100_000


async def ws(websocket):
    await websocket.accept()
    size = websocket.path_params["size"]
    message = messages[size]
    await websocket.send_text(message)
    # for offset in range(0, len(message), ws_chunk_size):
    #     chunk = message[offset : offset + ws_chunk_size]
    #     await websocket.send_text(chunk)
    await websocket.send_text("")
    await websocket.close()


async def echo(request):
    size = request.headers["Request-Size"]
    return PlainTextResponse(messages[size])


async def index(request):
    return PlainTextResponse('ok')


routes = [
    Route("/", endpoint=index),
    WebSocketRoute(r"/{path:path}/ws/{size}", endpoint=ws),
    # WebSocketRoute(r"/{path:path}/ws/large", endpoint=ws_large),
    Route("/{path:path}", endpoint=echo),
]

app = Starlette(routes=routes)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=9000, log_level="info")
