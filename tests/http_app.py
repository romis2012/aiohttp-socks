import asyncio

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route


async def ip(request: Request) -> PlainTextResponse:
    return PlainTextResponse(content=request.client.host)  # type:ignore[union-attr]


async def delay(request: Request) -> PlainTextResponse:
    seconds = request.path_params["seconds"]
    await asyncio.sleep(seconds)
    return PlainTextResponse(content="ok")


app = Starlette(
    debug=True,
    routes=[
        Route("/ip", ip),
        Route("/delay/{seconds:int}", delay),
    ],
)
