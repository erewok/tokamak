# Routing with Radix Trees

This project includes an [`AsgiRouter`](../reference/router/#tokamak.router.AsgiRouter) class which can be used to construct a routing tree.

A routing tree can be constructed of a combination static paths and regex patterns.

Here's an example of some paths:

- `"/doc/"`
- `"/doc/code_faq.html"`
- `"/info/{user}"`
- `"/info/{user}/project"`
- `"/info/{user}/project/{project}"`

In addition, a named regex pattern may be used:

- `"/regex/{name:[a-zA-Z]+}/test"`
- `"/optional/{name:[a-zA-Z]+}/{word}/plus/"`
- `"{uid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}}"`

However, the following pattern _will not_ match:

- `"/repos/{owner}/{repo}/{archive}_format/{ref}"`

The reason is `{archive}_format` includes a _greedy_ match `{archive}` which will match everything _up to_ the following slash.

## Constructing a Router

An AsgiRouter is a collection of routes:

```python
In [3]: from tokamak.router import AsgiRouter, Route

In [4]: async def some_handler(*args, **kwargs):
...        return "ok"

In [5]: router = AsgiRouter(routes=[
...        Route("/", handler=some_handler, methods=["GET"]),
... ])
```

**Note**: the `handler` can be _any_ callable.

It's also possible to use the method `add_route` to add more routes:

```python
In [6]: router.add_route(
...        Route("/files/{dir}/{filepath:*}", handler=some_handler, methods=["POST"])
... )
```

After that, we can search for a route:

```python
In [7]: router.get_route("/files/home/sshconfig")
Out[7]: (<tokamak.router.Route at 0x11009f940>,
 {'dir': 'home', 'filepath': 'sshconfig'})
```

A matching path from a call to `get_path` will return a `tuple` of a `Route` and the matched context:

```python
In [8]: route, context = router.get_route("/files/home/sshconfig")

In [9]: route.handler
Out[9]: <function __main__.some_handler(*args, **kwargs)>

In [11]: await route.handler()
Out[11]: 'ok'

In [12]: context
Out[12]: {'dir': 'home', 'filepath': 'sshconfig'}
```

**Note**: `UnknownEndpointError` will be returned for any route that doesn't match.

```python
In [13]: router.get_route("/files/home/sshconfig/unknown")
---------------------------------------------------------------------------
UnknownEndpointError                           Traceback (most recent call last)
Input In [13], in <cell line: 1>()
----> 1 router.get_route("/files/home/sshconfig/unknown")

File ~/open_source/tokamak/tokamak/router.py:135, in AsgiRouter.get_route(self, path)
    133 route, context = self.tree.get_handler(path)
    134 if not route:
--> 135     raise UnknownEndpointError(f"Unknown path: {path}")
    136 return route, context

UnknownEndpointError: Unknown path: /files/home/sshconfig/unknown
```
