from typing import Iterable, Optional, Tuple

try:
    import trio
except ImportError:
    trio = None


class Tokamak:
    def __init__(self, router=None, routes=None, background_task_limit=10):
        self.router = router
        self.routes = routes
        # The channel limit, not total limit; will apply back-pressure
        self.background_task_limit = background_task_limit

    async def lifespan(self, scope, receive, send):
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                print("Starting tokamak")
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                print("Shutting down tokamak")
                await send({"type": "lifespan.shutdown.complete"})
                return

    async def http(self, scope, receive, send):
        path: str = scope.get("path", "")
        route, context = self.router.get_route(path)

        bg_send_chan, bg_recv_chan = trio.open_memory_channel(
            self.background_task_limit
        )
        resp_send_chan, resp_recv_chan = trio.open_memory_channel(1)

        return await route(context, scope, receive, send)

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
