import json
from functools import partial

import trio
from hypercorn.config import Config
from hypercorn.trio import serve

from tokamak import AsgiRouter, Route
from tokamak.router import MethodNotAllowed, UnknownEndpoint


# # Fallback Handlers # #
async def method_not_allowed(scope, receive, send):
    await send(
        {
            "type": "http.response.start",
            "status": 405,
            "headers": [(b"Content-Type", b"text/html; charset=UTF-8")],
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": b"<html><body><h1>405 Method not allowed</h1></body></html>",
        }
    )


async def unknown_handler(scope, receive, send):
    await send(
        {
            "type": "http.response.start",
            "status": 404,
            "headers": [(b"Content-Type", b"text/html; charset=UTF-8")],
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": b"<html><body><h1>404 Not Found!</h1></body></html>",
        }
    )


# Real Application Handlers
async def index(path_context, scope, receive, send):
    message = await receive()
    if message["type"] == "http.request":
        body = message.get("body", b"")
        # here's our response:
        await send({"type": "http.response.start", "status": 200})
        await send({"type": "http.response.body", "body": body if body else b"OK"})
    elif message["type"] == "http.disconnect":
        print("Disconnected! ")


async def other_handler(path_context, scope, receive, send):
    context = bytes(json.dumps(path_context), encoding="utf-8")
    message = await receive()
    if message["type"] == "http.request":
        body = message.get("body", b"")
        await send({"type": "http.response.start", "status": 200})
        await send({"type": "http.response.body", "body": body if body else context})
    elif message["type"] == "http.disconnect":
        print("Disconnected! ")


# # Asgi Router Definition
ROUTER = AsgiRouter(
    routes=[
        Route("/", handler=index, methods=["GET"]),
        # Routes will match on regexes and bind to variables
        # given on the left side of the colon
        Route(
            "/other_handler/{name:[a-z1-9]+}",
            handler=other_handler,
            methods=["POST"],
        ),
    ]
)


async def asgi_app(scope, receive, send):
    path = scope.get("path", "")
    try:
        # Routers provider a `get_route` method
        # If no route is matched, they throw `UnknownEndpoint`
        # If a route is matched, we'll get path context and a handler
        handler, context = ROUTER.get_route(path)
    except UnknownEndpoint:
        await unknown_handler(scope, receive, send)
        return None

    try:
        # If a matched router doesn't handle this method
        # it will throw `MethodNotAllowed`
        await handler(context, scope, receive, send, method=scope.get("method"))
    except MethodNotAllowed:
        await method_not_allowed(scope, receive, send)
        return None


async def app_with_lifespan(scope, receive, send):
    if scope["type"] == "lifespan":
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return
    if scope["type"] == "http":
        return await asgi_app(scope, receive, send)


if __name__ == "__main__":
    config = Config()
    config.bind = ["localhost:8000"]
    trio.run(partial(serve, app_with_lifespan, config))
