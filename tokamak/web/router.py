from typing import Callable, Iterable, Optional
from tokamak.radix_tree import tree
from tokamak.web.request import Request
from tokamak.web.response import MethodNotAllowedResponse, UnknownResourceResponse
from tokamak.web import methods



async def unknown(request, **kwargs):
    await request.respond_with(UnknownResourceResponse)


async def method_not_allowed(request, **kwargs):
    await request.respond_with(MethodNotAllowedResponse)


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
        self.methods = set((m.upper() for m in methods)) if methods else {"GET"}

    def can_handle(self, method: str):
        return method in self.methods

    async def __call__(self, request: Request):
        if self.can_handle(request.scope.get(methods.SCOPE_METHOD_KEY)):
            return await self.handler(request)
        return await method_not_allowed(request)


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
            route = unknown
        return route, context
