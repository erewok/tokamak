# Tokamak

[![PyPI version fury.io](https://badge.fury.io/py/tokamak.svg)](https://pypi.python.org/pypi/tokamak/)
[![Documentation Status](https://readthedocs.org/projects/tokamak/badge/?version=latest)](https://tokamak.readthedocs.io/en/latest/?badge=latest)

Tokamak is a pure-Python router based on Radix trees intended for ASGI Python applications.

[[Read the documentation](https://tokamak.readthedocs.io/en/latest/)]

## Primary Project Goals

There are many HTTP routers based on radix trees available in other language communities, including Go, Javascript, Rust, and others. In Python, however, most open-source Python web frameworks instead utilize lists to store and look up HTTP routes.

The primary goal for this project is to provide a radix-tree-based router for Python web frameworks (or any custom ASGI or WSGI implementation).

**This library is _experimental_. Use at your own risk.**

### Other Goals

As a secondary goal, a minimal and highly experimental web framework is included an optional install in this library.

The reasons for including this web framework are as follows:

- It provides a convenient way to test the [`AsgiRouter`](/routing) class, and
- It allows the authors of this library to explore experimental ASGI-framework features, including request-cancellation, background task time-limits, and background task cancellation.

Developers should consider more fully-featured web frameworks _before_ this one and there are many to choose from:

- [Django](https://www.djangoproject.com/)
- [Flask](https://flask.palletsprojects.com/en/2.2.x/)
- [Quart](https://pgjones.gitlab.io/quart/)
- [Starlette](https://www.starlette.io/)
- [Tornado](https://www.tornadoweb.org/en/stable/)

## Installation

You can install `tokamak` with:

```sh
pip install tokamak
```

By default tokamak has no dependencies.

If you would like to try out the experimental web framework, you can install with optional extras `web`, which will include `trio`:

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
from tokamak.router import MethodNotAllowedError, UnknownEndpointError


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
        # If no route is matched, they throw `UnknownEndpointError`
        # If a route is matched, we'll get path context and a handler
        handler, context = ROUTER.get_route(path)
    except UnknownEndpointError:
        await unknown_handler(scope, receive, send)
        return None

    try:
        # If a matched router doesn't handle this method
        # it will throw `MethodNotAllowedError`
        await handler(context, scope, receive, send, method=scope.get("method"))
    except MethodNotAllowedError:
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

If we have these dependencies in our Python environment, we can run this simple script:

```sh
$ python examples/asgi_minimal.py
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

## For Contributors

This project uses `uv` for managing dependencies and virtual environments.

In addition, to contribute to this project, we recommend using `just`: https://github.com/casey/just

You can run various common workflows using the above tools, try the following:

```sh
❯ just
just --list
Available recipes:
    benchmark                         # Run the benchmark
    bootstrap default="3.12"          # Install dependencies used by this project
    build *args                       # Build the project as a package (uv build)
    check                             # Run code quality checks
    check-types                       # Run mypy checks
    ci-test coverage_dir='./coverage' # Run the project tests for CI environment (e.g. with code coverage)
    example name                      # Run an example
    format                            # Run the code formatter
    sync                              # Sync dependencies with environment
    test *args                        # Run all tests locally

❯ just check
+ uv run ruff check tokamak tests
All checks passed!

❯ just test
+ uv run pytest
...

```

### Examples

Runnable examples are provided in the [`examples` directory](https://github.com/erewok/tokamak/examples). In addition, this project includes a [`justfile`](./justfile) (see [just](https://github.com/casey/just)) for easily running examples.

For instance, you can run the experimental `tokamak` application with `trio` and `hypercorn` like so:

```sh
$  just example tokamak_app
uv run --extra examples python examples/tokamak_app.py
Installed 13 packages in 5.55s
========·°·°~> Starting tokamak °°···°°🚀···°°
[2024-11-19 09:01:24 -0800] [32768] [INFO] Running on http://127.0.0.1:8000 (CTRL + C to quit)
```

In a separate terminal, you can make various requests, such as the following:

```sh
❯ curl http://localhost:8000
ok

❯ curl http://localhost:8000/info/erik -d '{"some_data": "something"}'
{"received": {"some_data": "something"}}
```

Back in the first terminal, where you launched the example `tokamak` application, you should see the following:

```sh
❯ just example tokamak_app
uv run --extra examples python examples/tokamak_app.py
Installed 13 packages in 5.55s
========·°·°~> Starting tokamak °°···°°🚀···°°
[2024-11-19 09:01:24 -0800] [32768] [INFO] Running on http://127.0.0.1:8000 (CTRL + C to quit)
request.app.db={}, request.context={'user': 'erik'}, request.scope={'type': 'http', 'http_version': '1.1', 'asgi': {'spec_version': '2.1', 'version': '3.0'}, 'method': 'POST', 'scheme': 'http', 'path': '/info/erik', 'raw_path': b'/info/erik', 'query_string': b'', 'root_path': '', 'headers': [(b'host', b'localhost:8000'), (b'user-agent', b'curl/8.7.1'), (b'accept', b'*/*'), (b'content-length', b'26'), (b'content-type', b'application/x-www-form-urlencoded')], 'client': ('127.0.0.1', 63965), 'server': ('127.0.0.1', 8000), 'state': {}, 'extensions': {}, 'app': <tokamak.web.app.Tokamak object at 0x11865c4a0>}, headers=[(b'host', b'localhost:8000'), (b'user-agent', b'curl/8.7.1'), (b'accept', b'*/*'), (b'content-length', b'26'), (b'content-type', b'application/x-www-form-urlencoded')], qparams=b'', http_version='1.1', method='POST'
Sleeping 1s for total iterations: 0
Sleeping 1s for total iterations: 1
Sleeping 1s for total iterations: 2
```

## Benchmark

This project was iniatated around the time that the router for [`Werkzeug`](https://github.com/pallets/werkzeug.git) (which powers Flask) was rewritten as well. That router was redesigned to use a modified Radix Tree and so we created a benchmark to compare their implementation with this one.

To run the benchmark against Werkzeug `main`, run the following:

```sh
uv run --extra benchmarks python -m benchmark.compare_werkzeug
Path                                                                   | Ratio (percent difference from baseline)
Tokamak Tree is quicker: /users/{username}/following                                            | 0.64
Werkzeug Tree is quicker: /repos/{owner}/{repo}/downloads                                        | 0.80
Werkzeug Tree is quicker: /repos/{owner}/{repo}/hooks/{id}/pings                                 | 0.70
...

****** TIMING STATISTICS TOKAMAK FASTER THAN BASELINE ******
Better Total 5270
Best improvement (min vs baseline) 0.12283152787580384 for path /
Mean Improvement:  0.6338085629349435
Median Improvement:  0.618251951398763
Std Dev Improvements:  0.18516141441278625
Mean Path Length:  19.97020872865275
Mean Dynamic Segment Count:  0.6757115749525616
****** TIMING STATISTICS TOKAMAK END ******

****** TIMING STATISTICS WERKZEUG FASTER THAN BASELINE ******
Better Total 4730
Best improvement (min vs baseline) 0.23255522605196324 for path /repos/{owner}/{repo}/labels/{name}
Mean Improvement:  0.6003032685655771
Median Improvement:  0.5382439859668042
Std Dev Improvements:  0.20348200780749615
Mean Path Length:  36.14545454545455
Mean Dynamic Segment Count:  2.468076109936575
****** TIMING STATISTICS WERKZEUG END ******
```