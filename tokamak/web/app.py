from functools import partial
import logging
import traceback
from typing import Awaitable, Callable, Iterable, Optional, Tuple

from tokamak import methods, router
from tokamak.web.request import Request
from tokamak.web.response import Response

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


async def default_cancelled_request_handler(request: Request) -> Response:
    return Response(status_code=408, body=b"Request time limit exceeded")


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
        background_task_time_limit: Optional[int] = None,
        background_task_limit: int = 1000,
        request_time_limit: Optional[int] = None,
        cancelled_request_handler: Optional[
            Callable[[Request], Awaitable[Response]]
        ] = default_cancelled_request_handler,
        lifespan: Callable[["Tokamak", str], Awaitable["Tokamak"]] = lifespan_identity,
    ):
        self.router = router
        # Total background task limit; will apply back-pressure
        self.background_task_limit = background_task_limit
        # If set, will force each background task to run or cancel within this time limit (seconds)
        self.background_task_time_limit = background_task_time_limit
        # Channels for processing background tasks
        self.bg_send_chan, self.bg_recv_chan = trio.open_memory_channel(
            self.background_task_limit
        )
        # Lifespan callback should take this application instance and return it
        self.lifespan_func = lifespan
        # Request time limit means we'll cancel long-running requests (seconds)
        self.request_time_limit = request_time_limit
        # A special handler to invoke if a request has been cancelled
        self.cancelled_request_handler = cancelled_request_handler

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

    async def http(self, scope, receive, send, nursery):
        """ """
        path: str = scope.get("path", "")
        route, context = self.router.get_route(path)
        request = Request(context, scope, receive, path, self.bg_send_chan.clone())

        async with self.bg_send_chan, self.bg_recv_chan:
            # Any application handler we've been given may not have
            # a checkpoint so we insert an arbitrary one here
            await trio.sleep(0)

            request_cancelled = False
            # Run handler now and get `Response`
            if self.request_time_limit:
                with trio.move_on_after(
                    self.request_time_limit
                ) as request_cancel_scope:
                    async with trio.open_nursery():
                        response = await route(
                            request, method=scope.get(methods.SCOPE_METHOD_KEY)
                        )
                if request_cancel_scope.cancelled_caught:
                    request_cancelled = True
                    response = await self.cancelled_request_handler(request)
            else:
                response = await route(
                    request, method=scope.get(methods.SCOPE_METHOD_KEY)
                )

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
                await send({"type": "http.response.body", "body": response.body})

            # Run background
            if not request_cancelled:
                await self.process_background()

            return None

    async def process_background(self):
        async for background_task in self.bg_recv_chan.clone():
            if self.background_task_time_limit:
                with trio.move_on_after(self.background_task_time_limit):
                    async with trio.open_nursery() as nursery:
                        nursery.start_soon(background_task)
            else:
                await background_task()

    # async def ws(self, scope, receive, send, cancel_scope):
    #     """
    #     """
    #     path: str = scope.get("path", "")
    #     headers: Iterable[Tuple[bytes, bytes]] = scope.get("headers", [])
    #     qparams: Optional[bytes] = scope.get("query_string")
    #     http_version: Optional[str] = scope.get("http_version")
    #     method: Optional[str] = scope.get("method")

    #     bg_send_chan, bg_recv_chan = trio.open_memory_channel(
    #         self.background_task_limit
    #     )

    async def __call__(self, scope, receive, send):
        scope["app"] = self
        async with trio.open_nursery() as nursery:
            if scope["type"] == "lifespan":
                nursery.start_soon(self.lifespan, scope, receive, send)
            elif scope["type"] == "http":
                nursery.start_soon(self.http, scope, receive, send, nursery)
            elif scope["type"] == "websocket":
                nursery.start_soon(self.ws, scope, receive, send, nursery)
