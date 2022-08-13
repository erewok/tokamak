from functools import partial
import logging
import traceback
from typing import Awaitable, Callable, Optional

from tokamak import methods, router
from tokamak.web import errors
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


async def unknown_handler(scope, receive, send):
    """Unknown endpoint handler (404)"""
    await errors.UnknownResourceResponse(send)


class Tokamak:
    """
    When using the Tokamak App instance, you should define handlers
    that take a `tokamak.web.request.Request` instance.
    The `tokamak.web.request.Request` uses in-memory-channels to:
      - send back a Response, and
      - to schedule background work.

    Args:

        router (Optional[`tokamak.router.AsgiRouter`]): A router instance.
            str)`.
        background_task_time_limit (Optional[int]): Runtime Limit (in seconds) for background tasks.
        background_task_limit (int): Total limit of schedulable background tasks (backpressure will apply)
        request_time_limit (Optional[int]): Runtime Limit (in seconds) for request handlers.
        cancelled_request_handler (Optional[Callable]): Handler for cancelled requests
        lifespan (Callable): An async function with signature: `async def lifespan(tok: Tokamak, message_type:
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
        ] = errors.default_cancelled_request_handler,
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
        """
        Invoked for the lifespan activities.

        This method will be run on app start and app shutdown.
        """
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
                    await self.bg_send_chan.aclose()
                    await self.bg_recv_chan.aclose()

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
        """
        HTTP request handler.
        """
        path: str = scope.get("path", "")
        try:
            route, context = self.router.get_route(path)
        except router.UnknownEndpoint:
            await unknown_handler(scope, receive, send)
            return None

        # In order to support timeout-cancellations, we open a oneshot channel here
        # Request handlers must put their responses onto the channel
        async with trio.open_nursery() as nursery:
            (
                handler_response_send_chan,
                response_recv_chan,
            ) = trio.open_memory_channel(1)
            request = Request(
                context,
                scope,
                receive,
                path,
                self.bg_send_chan.clone(),
                handler_response_send_chan,
            )
            async with handler_response_send_chan, response_recv_chan:
                # Any application handler we've been given may not have
                # a checkpoint so we insert an arbitrary one here
                await trio.sleep(0)
                route_handling_fn = partial(
                    route, request, method=scope.get(methods.SCOPE_METHOD_KEY),
                )

                request_cancelled = False
                # Run handler now and get `Response`
                if self.request_time_limit:
                    with trio.move_on_after(
                        self.request_time_limit
                    ) as request_cancel_scope:
                        async with trio.open_nursery() as child_nursery:
                            child_nursery.start_soon(route_handling_fn)
                    if request_cancel_scope.cancelled_caught:
                        request_cancelled = True
                        cancellation_handler = partial(
                            self.cancelled_request_handler, request
                        )
                        nursery.start_soon(cancellation_handler)
                else:
                    nursery.start_soon(route_handling_fn)

                async for response in response_recv_chan:
                    await response(send)

            # Run background
            if not request_cancelled:
                nursery.start_soon(self.process_background)

        return None

    async def process_background(self):
        """Method that runs to process background requests"""
        async for background_task in self.bg_recv_chan.clone():
            if self.background_task_time_limit:
                with trio.move_on_after(self.background_task_time_limit):
                    async with trio.open_nursery() as nursery:
                        nursery.start_soon(background_task)
            else:
                await background_task()

    async def ws(self, scope, receive, send):
        """
        """
        path: str = scope.get("path", "")
        headers: Iterable[Tuple[bytes, bytes]] = scope.get("headers", [])
        qparams: Optional[bytes] = scope.get("query_string")
        http_version: Optional[str] = scope.get("http_version")
        method: Optional[str] = scope.get("method")

        bg_send_chan, bg_recv_chan = trio.open_memory_channel(
            self.background_task_limit
        )

    async def __call__(self, scope, receive, send):
        """A Tokamak application will be invoked here on each request"""
        scope["app"] = self
        async with trio.open_nursery() as nursery:
            if scope["type"] == "lifespan":
                nursery.start_soon(self.lifespan, scope, receive, send)
            elif scope["type"] == "http":
                nursery.start_soon(self.http, scope, receive, send)
            elif scope["type"] == "websocket":
                nursery.start_soon(self.ws, scope, receive, send)
