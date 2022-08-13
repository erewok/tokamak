# Tokamak Experimental Web Framework

This library can be installed with the extra-feature "web" in order to use the experimental web framework.

This web framework is included as an optional install in this library for two reasons:

- It provides a convenient way to test the [`AsgiRouter`](/routing) class, and
- It allows this library to explore experimental ASGI-framework features, including request-cancellation, background task time-limits, and background task cancellation.

This page describes the `Tokamak` web application. Its behavior is highly limited compared to feature-complete web frameworks. For instance, it **does not** include the following features:

- Error handling
- Middleware

## `Tokamak` Application Example

Following is an example of using the `Tokamak` application in order to build a basic web server.

### Application Imports

First, here are the imports we'll use for this sample application as well as setting up a logger and a fake database object. These will not be repeated below for simplicity:

```python
import json
import logging
from functools import partial
from typing import Iterable, Optional, Tuple

import trio
from hypercorn.config import Config
from hypercorn.trio import serve

from tokamak import AsgiRouter, Route
from tokamak.web import Request, Response, Tokamak

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
logger.addHandler(sh)
# Fake database
DB = {}
```

### Application Handlers and Background Task

After that, we can construct some handlers, a lifespan function, and a background task, all of which we will use below:

```python
async def lifespan(app: Tokamak, message_type: str = "") -> Tokamak:
    """This is a demonstration of a lifespan async function.

    This function will be invoked on application startup _and_ shutdown.
    """
    if message_type == Tokamak.LIFESPAN_STARTUP:
        app.db = DB
    elif message_type == Tokamak.LIFESPAN_SHUTDOWN:
        app.db = None
    return app

async def timeout_request_test(request: Request):
    """This request will demonstrate our application timeout response"""
    await trio.sleep(2)
    await request.respond_with(Response(body=b"ok"))


async def bg_task(arg1=None):
    for n in range(5):
        logger.info(f"Sleeping 1s for total iterations: {n}")
        await trio.sleep(1)
    logger.info(f"Background DONE SLEEPING, with arg1 '{arg1}'")


async def generic_handler(request: Request):
    headers: Iterable[Tuple[bytes, bytes]] = request.scope.get("headers", [])
    qparams: Optional[bytes] = request.scope.get("query_string")
    http_version: Optional[str] = request.scope.get("http_version")
    method: Optional[str] = request.scope.get("method")

    # Dump out contents of request
    logger.info(
        (
            f"{request.app.db=}, {request.context=}, "
            f"{request.scope=}, {headers=}, {qparams=}, {http_version=}, {method=}"
        )
    )
    message = await request.receive()
    body = message.get("body") or b"{}"
    payload = json.dumps({"received": json.loads(body)}).encode("utf-8")
    request.app.db[request.path] = payload
    await request.register_background(partial(bg_task, arg1="some kwarg"))
    await request.respond_with(Response(body=payload))
```

### Routes and Tokamak Application

Now, we can build a `Tokamak` application:

```python

ROUTES = [
    Route("/", handler=generic_handler, methods=["GET"]),
    Route("/timeout", handler=timeout_request_test, methods=["GET"]),
]

if __name__ == "__main__":
    config = Config()
    config.bind = ["localhost:8000"]
    app = Tokamak(
        router=AsgiRouter(routes=ROUTES),
        request_time_limit=1,
        background_task_time_limit=3,
        lifespan=lifespan,
    )
    trio.run(serve, app, config)
```

**Note**: our `Tokamak` application has the following time-limits applied:

- `request_time_limit`: 1 second
- `background_task_time_limit`: 3 seconds

When we run our application and request it from another terminal with `curl -i http://localhost:8000`, we will see that our background tasks gets limited to 3 seconds total:

```sh
❯ poetry run python examples/simple_app.py
========·°·°~> Starting tokamak °°···°°🚀···°°
[2022-08-12 18:55:34 -0700] [27155] [INFO] Running on http://127.0.0.1:8000 (CTRL + C to quit)
request.app.db={}, request.context={}, request.scope={'type': 'http', 'http_version': '1.1', 'asgi': {'spec_version': '2.1', 'version': '3.0'}, 'method': 'GET', 'scheme': 'http', 'path': '/', 'raw_path': b'/', 'query_string': b'', 'root_path': '', 'headers': <Headers([(b'host', b'localhost:8000'), (b'user-agent', b'curl/7.81.0'), (b'accept', b'*/*')])>, 'client': ('127.0.0.1', 64918), 'server': ('127.0.0.1', 8000), 'extensions': {}, 'app': <tokamak.web.app.Tokamak object at 0x110827100>}, headers=<Headers([(b'host', b'localhost:8000'), (b'user-agent', b'curl/7.81.0'), (b'accept', b'*/*')])>, qparams=b'', http_version='1.1', method='GET'
Sleeping 1s for total iterations: 0
Sleeping 1s for total iterations: 1
Sleeping 1s for total iterations: 2
```

In addition, we can see the timeout behavior if we request our `/timeout` endpoint:

```sh
❯ curl -i http://localhost:8000/timeout
HTTP/1.1 408
content-length: 27
content-type: text/plain; charset=utf-8
date: Sat, 13 Aug 2022 01:55:40 GMT
server: hypercorn-h11

Request time limit exceeded
```
