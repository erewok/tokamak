import json
from typing import Iterable, Optional, Tuple

from hypercorn.config import Config
from hypercorn.trio import serve
import trio

from tokamak.web import AsgiRouter, Request, Response, Route, Tokamak


TEST_ROUTES = [
    "/",
    "/contact/",
    "/co",
    "/c",
    "/cmd/{tool}/{sub}",
    "/cmd/{tool}/",
    "/dcb/{tool}/",  # similar structure to test if ordering matters
    "/dcb/{tool}/{sub}",
    "/a/b/c/d/e/f",
    "/a/b/c/d/e/g",
    "/a/b/c/d/e/h",
    "/a/b/c/d/e/f/g/h",
    "/src/{filepath:*}",
    "/src/data",
    "/search/",
    "/search/{query}",
    "/user_{name}",
    "/user_{name}/dept",
    "/files/{dir}/{filepath:*}",
    "/doc/",
    "/doc/code_faq.html",
    "/doc/code1.html",
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
    "/γένωνται/{name}/aaa",
    "/darüber/schloß",
    "/darüber/schloß/ritter",
    "/hello/test",
    "/hello/{name}",
]


async def handler(request: Request):
    headers: Iterable[Tuple[bytes, bytes]] = request.scope.get("headers", [])
    qparams: Optional[bytes] = request.scope.get("query_string")
    http_version: Optional[str] = request.scope.get("http_version")
    method: Optional[str] = request.scope.get("method")
    print(request.context, request.scope, headers, qparams, http_version, method)

    message = await request.receive()
    body = message.get("body") or b"{}"
    payload = json.dumps({"received": json.loads(body)}).encode("utf-8")
    await request.respond_with(Response(body=payload))


def make_router():
    return AsgiRouter(
        routes=[Route(path=route, handler=handler) for route in TEST_ROUTES]
    )


if __name__ == "__main__":
    config = Config()
    config.bind = ["localhost:8000"]
    trio.run(serve, Tokamak(router=make_router()), config)
