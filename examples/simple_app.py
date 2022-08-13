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
