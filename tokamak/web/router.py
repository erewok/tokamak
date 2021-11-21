from typing import Callable, Iterable, Optional

from tokamak.radix_tree import tree
from tokamak.web import methods as tokmethods


class RouterError(ValueError):
    pass


class UnknownEndpoint(RouterError):
    pass


class MethodNotAllowed(RouterError):
    pass


class Route:
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
