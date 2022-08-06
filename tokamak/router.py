from typing import Callable, Iterable, Optional

from tokamak import methods as tokmethods
from tokamak.radix_tree import tree


class RouterError(ValueError):
    pass


class UnknownEndpoint(RouterError):
    pass


class MethodNotAllowed(RouterError):
    pass


class Route:
    """
    A Route for a Tokamak Application represents:
      - a path,
      - a request method, and
      - a handler dedicated to requests that match that path and method.
    """

    def __init__(
        self,
        path: str = "",
        handler: Optional[Callable] = None,
        methods: Optional[Iterable[str]] = None,
    ):
        if handler is None:
            raise ValueError("Missing `handler` function for path: {}".format(path))
        self.handler = handler
        self.path = path
        self.methods = (
            set((m.upper() for m in methods))
            if methods
            else {tokmethods.Method.GET.value}
        )

    def can_handle(self, method: str):
        return method in self.methods

    async def __call__(self, *args, method=tokmethods.Method.GET.value, **kwargs):
        if not self.can_handle(method):
            raise MethodNotAllowed(f"{method} not allowed for {self.path}")
        return await self.handler(*args, **kwargs)


class AsgiRouter:
    """
    A AsgiRouter for a Tokamak Application is one or more `Route`s
    with an optional configuration for matching trailing slashes or not.

    Example:
        async def some_handler(request: Request):
            headers: Iterable[Tuple[bytes, bytes]] = request.scope.get("headers", [])
            qparams: Optional[bytes] = request.scope.get("query_string")
            http_version: Optional[str] = request.scope.get("http_version")
            method: Optional[str] = request.scope.get("method")
            print(request.context, request.scope, headers, qparams, http_version, method)

            message = await request.receive()
            body = message.get("body") or b"{}"
            payload = json.dumps({"received": json.loads(body)}).encode("utf-8")
            await request.respond_with(Response(body=payload))
            await request.register_background(partial(bg_task, arg1="some kwarg"))


        AsgiRouter(routes=[
            Route("/", handler=some_handler, methods=["GET"]),
            Route("/files/{dir}/{filepath:*}", handler=some_handler, methods=["POST"]),

        ])

    A dynamic route takes a name for the captured variable and a regex matcher,
    like so: `"/regex/{name:[a-zA-Z]+}/test"`

    The values matched in paths are always returned in the `context` as strings.
    """

    def __init__(
        self,
        routes: Optional[Iterable[Route]] = None,
        trailing_slash_match: tree.TrailingSlashMatch = tree.TrailingSlashMatch.RELAXED,
    ):
        self.tree = tree.Tree(trailing_slash_match=trailing_slash_match)
        if routes:
            self.build_route_tree(routes)

    def build_route_tree(self, routes: Iterable[Route]):
        for route in routes:
            self.add_route(route)

    def add_route(self, route: Route):
        self.tree.insert(route.path, route)

    def get_route(self, path):
        route, context = self.tree.get_handler(path)
        if not route:
            raise UnknownEndpoint(f"Unknown path: {path}")
        return route, context
