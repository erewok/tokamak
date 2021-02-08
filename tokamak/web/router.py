from typing import Callable, Iterable, Optional
from tokamak.radix_tree import tree
from tokamak.web import methods


class Response:
    def __init__(self, body: bytes, status_code=200):
        self.body = body
        self.status_code = status_code

    async def __call__(self, context, scope, receive, send, *args, **kwargs):
        await send({"type": "http.response.start", "status": self.status_code})
        await send({"type": "http.response.body", "body": self.body})
        return self.body


UnknownResourceResponse = Response(b"Unknown Resource", status_code=404)
MethodNotAllowedResponse = Response(b"Method not allowed", status_code=405)


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

    async def __call__(self, context, scope, receive, send):
        if self.can_handle(scope.get(methods.SCOPE_METHOD_KEY)):
            return await self.handler(context, scope, receive, send)
        return await MethodNotAllowedResponse(context, scope, receive, send)


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
            route = UnknownResourceResponse
        return route, context
