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


async def error_lifespan(app: Tokamak, message_type: str = "") -> Tokamak:
    if message_type == Tokamak.LIFESPAN_STARTUP:
        raise ValueError("Startup blew up")
    elif message_type == Tokamak.LIFESPAN_SHUTDOWN:
        raise ValueError("Startup blew up")
    return app


async def lifespan(app: Tokamak, message_type: str = "") -> Tokamak:
    if message_type == Tokamak.LIFESPAN_STARTUP:
        app.db = DB
    elif message_type == Tokamak.LIFESPAN_SHUTDOWN:
        app.db = None
    return app


async def bg_task(arg1=None):
    for n in range(5):
        logger.info(f"Sleeping 1s for total iterations: {n}")
        await trio.sleep(1)
    logger.info(f"Background DONE SLEEPING, with arg1 '{arg1}'")


async def index(request: Request):
    await request.respond_with(Response(body=b"ok"))


async def context_matcher(request: Request):
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


async def timeout_request_test(request: Request):
    await trio.sleep(2)
    await request.respond_with(Response(body=b"ok"))


ROUTES = [
    Route("/", handler=index, methods=["GET"]),
    Route("/timeout", handler=timeout_request_test, methods=["GET"]),
    *[
        Route(path, handler=context_matcher, methods=["GET", "POST"])
        for path in [
            "/files/{dir}/{filepath:*}",
            "/info/{user}",
            "/info/{user}/project",
            "/info/{user}/project/{project}",
            "/info/{user}/project/{project}/dept",
            "/info/{user}/project/{project}/dept/{dept}",
            "/regex/{name:[a-zA-Z]+}/test",
            (
                "/optional/{name:[a-zA-Z]+}/{word}/plus/"
                "{uid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}}"
            ),
        ]
    ],
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
