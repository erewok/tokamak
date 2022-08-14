from typing import Callable, Iterable, Optional, Tuple

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

    Example:

        Route("/", handler=any_async_handler, methods=["GET", "POST"])

    Args:
        path (str): The http path to add to the router.
        handler (Callable): The async handler (any awaitable callable) to invoke on path match
        methods (List[str]): A list of accepted methods for this endpoint
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
    An AsgiRouter for a Tokamak Application is one or more `Route`s
    with an optional configuration for matching trailing slashes or not.

    Example:
        We can define an endpoint handler to associate with any route:

            async def some_handler(scope, receive, send):
                message = await receive()
                body = message.get("body") or b"{}"
                payload = json.dumps({"received": json.loads(body)}).encode("utf-8")
                return Response(body=payload)

        After that, we can include associate the handler with an endpoint:

            AsgiRouter(routes=[
                Route("/", handler=some_handler, methods=["GET"]),
                Route("/files/{dir}/{filepath:*}", handler=some_handler, methods=["POST"]),

            ])

    A dynamic route takes a name for the captured variable and a regex matcher,
    like so: `"/regex/{name:[a-zA-Z]+}/test"`

    The values matched in paths are always returned in the `context` as strings.

    Args:
        routes (Iterable[Route]): An optional iterable of routes to add.
        trailing_slash_match (TrailingSlashMatch): Strictness property for trailing slashes
    """

    def __init__(
        self,
        routes: Optional[Iterable[Route]] = None,
        trailing_slash_match: tree.TrailingSlashMatch = tree.TrailingSlashMatch.RELAXED,
    ):
        self.tree = tree.Tree(trailing_slash_match=trailing_slash_match)
        if routes:
            self.build_route_tree(routes)

    def build_route_tree(self, routes: Iterable[Route]) -> None:
        """
        Builds the full routing tree.

        Args:
            routes (Iterable[Route]): An iterable of routes to add.
        """
        for route in routes:
            self.add_route(route)

    def add_route(self, route: Route) -> None:
        """
        Adds a single route to the tree.

        Args:
            route (Route): A route to add.
        """
        self.tree.insert(route.path, route)

    def get_route(self, path: str) -> Tuple[Route, dict[str, str]]:
        """
        Search for a matching route by path.

        Args:
            path (str): The path to search for.

        Returns:
            Tuple[Router, context-dictionary]

        Raises `UnknownEndpoint` if no path matched.
        """
        route, context = self.tree.get_handler(path)
        if not route:
            raise UnknownEndpoint(f"Unknown path: {path}")
        return route, context
