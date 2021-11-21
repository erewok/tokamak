import logging
from functools import wraps
from typing import Iterable, Optional, Tuple

import trio

from tokamak.web import methods, router
from tokamak.web.request import Request

logger = logging.getLogger("tokamak")


class Tokamak:
    """
    When using the Tokamak App instance, you should define handlers
    that take a `tokamak.web.request.Request` instance, which uses
    in-memory-channels to send back a Response and to schedule background
    work.
    """

    def __init__(
        self,
        router: Optional[router.AsgiRouter] = None,
        background_task_limit: int = 10,
    ):
        self.router = router
        # The channel limit, not total limit; will apply back-pressure
        self.background_task_limit = background_task_limit

    async def lifespan(self, scope, receive, send):
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                logger.warn("========·°·°~> Starting tokamak °°···°°🚀···°° ")
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                logger.warn("~°°···°°°~ Shutting down tokamak ~°°···🚉···°°°~ ")
                await send({"type": "lifespan.shutdown.complete"})
                return

    async def http(self, scope, receive, send):
        path: str = scope.get("path", "")
        route, context = self.router.get_route(path)

        bg_send_chan, bg_recv_chan = trio.open_memory_channel(
            self.background_task_limit
        )
        # http allows one response: what about streaming?
        resp_send_chan, resp_recv_chan = trio.open_memory_channel(1)

        request = Request(context, scope, receive, resp_send_chan, bg_send_chan)

        await route(request, method=scope.get(methods.SCOPE_METHOD_KEY))

        async with resp_recv_chan:
            async for response in resp_recv_chan:
                await send(
                    {
                        "type": "http.response.start",
                        "status": response.status_code,
                        "headers": response.raw_headers,
                    }
                )
                if response.streaming:
                    async for chunk in response.streaming_body:
                        await send(
                            {
                                "type": "http.response.body",
                                "body": chunk,
                                "more_body": True,
                            }
                        )
                    await send(
                        {"type": "http.response.body", "body": b"", "more_body": False}
                    )
                else:
                    await send({"type": "http.response.body", "body": response.body})

        async with bg_recv_chan:
            async for background_task in bg_recv_chan:
                await background_task()

        return None

    async def ws(self, scope, receive, send):
        path: str = scope.get("path", "")
        headers: Iterable[Tuple[bytes, bytes]] = scope.get("headers", [])
        qparams: Optional[bytes] = scope.get("query_string")
        http_version: Optional[str] = scope.get("http_version")
        method: Optional[str] = scope.get("method")

        bg_send_chan, bg_recv_chan = trio.open_memory_channel(
            self.background_task_limit
        )
        resp_send_chan, resp_recv_chan = trio.open_memory_channel(1)

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            return await self.lifespan(scope, receive, send)
        elif scope["type"] == "http":
            return await self.http(scope, receive, send)
        elif scope["type"] == "websocket":
            return await self.ws(scope, receive, send)
