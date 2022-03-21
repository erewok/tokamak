# Tokamak

> In a star as in a fusion device, plasmas provide the environment in which light elements can fuse and yield energy.

Tokamak is a router based on Radix trees intended for ASGI Python applications.

## Project Goals (Why Did You Build This?)

This project was created to fill a gap in the Python ecosystem. There is a variety of HTTP routers based on radix trees available in other language communities, including Go, Javascript, Rust, and others. In Python, however, no such library exists and most open-source Python web frameworks instead utilize lists to store and look up HTTP routes.

The primary goal for this project is to provide a radix-tree-based router for Python web frameworks (or any custom ASGI or WSGI implementation).

**This library is currently considered to be _experimental_.**

As a secondary goal, a minimal web framework may in the future also be provided for building web applications in order to explore this space. However, more fully featured frameworks should be considered before this one. Producing a feature-complete web framework is _not_ a primary goal of this project.

## Installation

You can install `tokamak` with:

```sh
pip install tokamak
```

By default tokamak has no dependencies. If you would like to try out the experimental web framework, you can install with optional extras `web`, which will include `trio`:

```sh
$ pip install "tokamak[web]"
...
```

## Usage

This library provides a radix tree implementation and a basic `AsgiRouter` router implementation for low-level ASGI applications. You can use the `AsgiRouter` class as follows.

First, we start with some with some imports and some fallback handlers:

```python
from hypercorn.config import Config
from hypercorn.trio import serve
import trio

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
```

Next we'll build two different application endpoint handlers. These do roughly the same thing, so this is purely for demonstration purposes:

```python
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
```

Finally, we can build an `AsgiRouter` and a working ASGI app, like this:

```python
# `AsgiRouter` and `Route` class provided by this library
ROUTER = AsgiRouter(
    routes=[
        Route("/", handler=index, methods=["GET"]),
        # Routes will match on regexes and bind to variables
        # given on the left side of the colon
        Route(
            "/other_handler/{name:[a-z1-9]+}", handler=other_handler, methods=["POST"],
        ),
    ]
)

# This is a basic implementation of the ASGI spec
# See: https://asgi.readthedocs.io/en/latest/specs/main.html
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
```

Finally, to run our ASGI app, we'll add the following:

```python

if __name__ == "__main__":
    config = Config()
    config.bind = ["localhost:8000"]
    trio.run(partial(serve, app_with_lifespan, config))
```

This example relies on the following dependencies:

- hypercorn
- trio

If we have these dependencies in our Python environment, we can this simple script:

```sh
$ poetry run python examples/asgi_minimal.py
[2022-03-20 16:59:58 -0700] [91988] [INFO] Running on http://127.0.0.1:8000 (CTRL + C to quit)
```

In a separate terminal, we can try it out like so:

```sh
❯ curl http://localhost:8000/
OK

# No capital letters matched
❯ curl -XPOST http://localhost:8000/other_handler/bla1AA
<html><body><h1>404 Not Found!</h1></body></html>

# GET not POST -> 405
❯ curl http://localhost:8000/other_handler/bla
<html><body><h1>405 Method not allowed</h1></body></html>

# Success
❯ curl -XPOST http://localhost:8000/other_handler/bla1
{"name": "bla1"}
```

**Note**: that our regex path _does not_ match capital letters, so that request 404s.

## Examples

Runnable examples are provided in the [`./examples`](./examples/) directory. For instance, you can run an example application with `trio` and `hypercorn` like so:

```sh
$ poetry install -E "full"
Installing dependencies from lock file

Package operations: 8 installs, 0 updates, 0 removals

  • Installing h11 (0.13.0)
  • Installing hpack (4.0.0)
  • Installing hyperframe (6.0.1)
  • Installing h2 (4.1.0)
  • Installing priority (2.0.0)
  • Installing toml (0.10.2)
  • Installing wsproto (1.1.0)
  • Installing hypercorn (0.13.2)

Installing the current project: tokamak (0.2.1)
❯ poetry run python examples/tokamak_app.py
========·°·°~> Starting tokamak °°···°°🚀···°°
[2022-03-20 11:05:01 -0700] [63023] [INFO] Running on http://127.0.0.1:8000 (CTRL + C to quit)
```

In a separate terminal, you can make various requests, such as the following:

```sh
❯ curl http://localhost:8000
{"received": {}}

❯ curl http://localhost:8000/info/erik -d '{"some_data": "something"}'
{"received": {"some_data": "something"}}
```

Back in the first terminal, where you launched the example `tokamak` application, you should see the following:

```sh
❯ poetry run python examples/tokamak_app.py
========·°·°~> Starting tokamak °°···°°🚀···°°
[2022-03-20 11:05:01 -0700] [63023] [INFO] Running on http://127.0.0.1:8000 (CTRL + C to quit)
{} {'type': 'http', 'http_version': '1.1', 'asgi': {'spec_version': '2.1', 'version': '3.0'}, 'method': 'GET', 'scheme': 'http', 'path': '/', 'raw_path': b'/', 'query_string': b'', 'root_path': '', 'headers': <Headers([(b'host', b'localhost:8000'), (b'user-agent', b'curl/7.81.0'), (b'accept', b'*/*')])>, 'client': ('127.0.0.1', 55379), 'server': ('127.0.0.1', 8000), 'extensions': {}} <Headers([(b'host', b'localhost:8000'), (b'user-agent', b'curl/7.81.0'), (b'accept', b'*/*')])> b'' 1.1 GET
Sleeping 1s for total seconds: 0
Sleeping 1s for total seconds: 1
Sleeping 1s for total seconds: 2
Sleeping 1s for total seconds: 3
Sleeping 1s for total seconds: 4
{'user': 'erik'} {'type': 'http', 'http_version': '1.1', 'asgi': {'spec_version': '2.1', 'version': '3.0'}, 'method': 'POST', 'scheme': 'http', 'path': '/info/erik', 'raw_path': b'/info/erik', 'query_string': b'', 'root_path': '', 'headers': <Headers([(b'host', b'localhost:8000'), (b'user-agent', b'curl/7.81.0'), (b'accept', b'*/*'), (b'content-length', b'26'), (b'content-type', b'application/x-www-form-urlencoded')])>, 'client': ('127.0.0.1', 55386), 'server': ('127.0.0.1', 8000), 'extensions': {}} <Headers([(b'host', b'localhost:8000'), (b'user-agent', b'curl/7.81.0'), (b'accept', b'*/*'), (b'content-length', b'26'), (b'content-type', b'application/x-www-form-urlencoded')])> b'' 1.1 POST
Sleeping 1s for total seconds: 0
Sleeping 1s for total seconds: 5
Sleeping 1s for total seconds: 1
Sleeping 1s for total seconds: 6
Sleeping 1s for total seconds: 2
Sleeping 1s for total seconds: 7
Sleeping 1s for total seconds: 3
Sleeping 1s for total seconds: 8
```
