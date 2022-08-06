import logging
import traceback
from typing import Awaitable, Callable, Iterable, Optional, Tuple

from tokamak import methods, router
from tokamak.web.request import Request

logger = logging.getLogger("tokamak")

try:
    import trio
except ImportError:
    logger.error(
        (
            "To use Tokamak's web properties, "
            "the library must be installed with option [web]"
        )
    )
    raise


async def lifespan_identity(app: "Tokamak", message_type: str = "") -> "Tokamak":
    """A default implementation of lifespan: the identity function"""
    return app


class Tokamak:
    """
    When using the Tokamak App instance, you should define handlers
    that take a `tokamak.web.request.Request` instance.
    The `tokamak.web.request.Request` uses in-memory-channels to:
      - send back a Response, and
      - to schedule background work.

    **Parameters:**

    * **router** - a `tokamak.router.AsgiRouter` instance.
    * **lifespan** - an async function with signature:
    `async def lifespan(tok: Tokamak, message_type: str)`.
    * **background_task_limit** - Limit for background tasks allowed for
    _each_ handler before back-pressure is applied.
    """

    LIFESPAN_STARTUP = "lifespan.startup"
    LIFESPAN_SHUTDOWN = "lifespan.shutdown"

    def __init__(
        self,
        router: Optional[router.AsgiRouter] = None,
        background_task_limit: int = 1000,
        lifespan: Callable[["Tokamak", str], Awaitable["Tokamak"]] = lifespan_identity,
    ):
        self.router = router
        # Total background task limit; will apply back-pressure
        self.background_task_limit = background_task_limit
        # Lifespan callback should take this application instance and return it
        self.lifespan_func = lifespan
        self.bg_send_chan, self.bg_recv_chan = trio.open_memory_channel(
            self.background_task_limit
        )

    async def lifespan(self, scope, receive, send):
        while True:
            message = await receive()
            if message["type"] == self.LIFESPAN_STARTUP:
                logger.warn("========·°·°~> Starting tokamak °°···°°🚀···°° ")
                try:
                    await self.lifespan_func(self, message_type=message["type"])
                except Exception:
                    await send(
                        {
                            "type": "lifespan.startup.failed",
                            "message": traceback.format_exc(),
                        }
                    )
                else:
                    await send({"type": "lifespan.startup.complete"})
            elif message["type"] == self.LIFESPAN_SHUTDOWN:
                logger.warn("~°°···°°°~ Shutting down tokamak ~°°···🚉···°°°~ ")
                try:
                    await self.lifespan_func(self, message_type=message["type"])
                except Exception:
                    await send(
                        {
                            "type": "lifespan.shutdown.failed",
                            "message": traceback.format_exc(),
                        }
                    )
                else:
                    await send({"type": "lifespan.shutdown.complete"})
                return None

    async def http(self, scope, receive, send):
        path: str = scope.get("path", "")
        route, context = self.router.get_route(path)

        resp_send_chan, resp_recv_chan = trio.open_memory_channel(1)

        request = Request(
            context, scope, receive, path, resp_send_chan, self.bg_send_chan
        )

        async with self.bg_send_chan, self.bg_recv_chan:
            async with resp_recv_chan:
                # Run handler
                await route(request, method=scope.get(methods.SCOPE_METHOD_KEY))
                # Send response to client
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
                            {
                                "type": "http.response.body",
                                "body": b"",
                                "more_body": False,
                            }
                        )
                    else:
                        await send(
                            {"type": "http.response.body", "body": response.body}
                        )
            # Run background
            async for background_task in self.bg_recv_chan:
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
        scope["app"] = self
        async with trio.open_nursery() as nursery:
            if scope["type"] == "lifespan":
                nursery.start_soon(self.lifespan, scope, receive, send)
            elif scope["type"] == "http":
                nursery.start_soon(self.http, scope, receive, send)
            elif scope["type"] == "websocket":
                nursery.start_soon(self.ws, scope, receive, send)
