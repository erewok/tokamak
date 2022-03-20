import json
from typing import Iterable, Optional, Tuple

from hypercorn.config import Config
from hypercorn.trio import serve
import trio

from tokamak.web import AsgiRouter, Request, Response, Route, Tokamak


async def bg_task(arg1=None):
    for n in range(10):
        print(f"Sleeping 1s for total seconds: {n}")
        await trio.sleep(1)
    print("Background DONE SLEEPING, with arg1", arg1)


async def index(request: Request):
    headers: Iterable[Tuple[bytes, bytes]] = request.scope.get("headers", [])
    qparams: Optional[bytes] = request.scope.get("query_string")
    http_version: Optional[str] = request.scope.get("http_version")
    method: Optional[str] = request.scope.get("method")
    print(request.context, request.scope, headers, qparams, http_version, method)

    message = await request.receive()
    body = message.get("body") or b"{}"
    payload = json.dumps({"received": json.loads(body)}).encode("utf-8")
    await request.respond_with(Response(body=payload))
    await request.register_background(bg_task)


async def context_matcher(request: Request):
    headers: Iterable[Tuple[bytes, bytes]] = request.scope.get("headers", [])
    qparams: Optional[bytes] = request.scope.get("query_string")
    http_version: Optional[str] = request.scope.get("http_version")
    method: Optional[str] = request.scope.get("method")
    print(request.context, request.scope, headers, qparams, http_version, method)

    message = await request.receive()
    body = message.get("body") or b"{}"
    payload = json.dumps({"received": json.loads(body)}).encode("utf-8")
    await request.respond_with(Response(body=payload))
    await request.register_background(bg_task)


ROUTES = [
    Route("/", handler=index, methods=["GET"]),
    *[
        Route(path, handler=context_matcher, methods=["POST"])
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
    trio.run(serve, Tokamak(router=AsgiRouter(routes=ROUTES)), config)
