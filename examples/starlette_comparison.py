import json
import logging
from typing import Iterable, Optional, Tuple

import trio
from hypercorn.config import Config
from hypercorn.trio import serve
from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
logger.addHandler(sh)
# Fake database
DB = {}

TEST_ROUTES = [
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


async def bg_task(arg1=None):
    for n in range(5):
        logger.info(f"Sleeping 1s for total iterations: {n}")
        await trio.sleep(1)
    logger.info(f"Background DONE SLEEPING, with arg1 '{arg1}'")


async def index(request):
    return PlainTextResponse("ok")


async def context_matcher(request: Request):
    headers: Iterable[Tuple[bytes, bytes]] = request.scope.get("headers", [])
    qparams: Optional[bytes] = request.scope.get("query_string")
    http_version: Optional[str] = request.scope.get("http_version")
    method: Optional[str] = request.scope.get("method")

    task = BackgroundTask(bg_task, arg1="some kwarg")
    # Dump out contents of request
    logger.info(
        (
            f"{request.app.db=}, {request.path_params=}, "
            f"{request.scope=}, {headers=}, {qparams=}, {http_version=}, {method=}"
        )
    )
    message = await request.receive()
    body = message.get("body") or b"{}"
    payload = {"received": json.loads(body)}
    request.app.db[request.url.path] = payload
    return JSONResponse(payload, background=task)


def make_router():
    return [
        Route("/", endpoint=index, methods=["GET"]),
        *[Route(route, endpoint=context_matcher) for route in TEST_ROUTES],
    ]


if __name__ == "__main__":
    config = Config()
    config.bind = ["localhost:8000"]
    app = Starlette(routes=make_router())
    app.db = DB
    trio.run(serve, app, config)
