from random import choice

from tokamak.router import AsgiRouter, Route


async def handler(request):
    return None


def test_router(large_path_list):
    router = AsgiRouter()
    for path in large_path_list:
        router.add_route(Route(path, handler=handler, methods=["GET"]))
    for _ in range(50):
        path = choice(large_path_list)
        assert router.get_route(path)
