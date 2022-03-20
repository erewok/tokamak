# Tokamak

> In a star as in a fusion device, plasmas provide the environment in which light elements can fuse and yield energy.

Tokamak is a router based on Radix trees intended for ASGI Python applications.

## Project Goals (Why Did You Build This?)

This project was created to fill a gap in the Python ecosystem. In various other language communities, including Go, Javascript, and others, HTTP routers based on radix trees have been provided by open-source projects. In Python, no such library exists and most open-source Python web frameworks utilize lists to store and look up HTTP routes.

Thus, this project exists to provide a radix-tree-based router for Python web frameworks (or any custom ASGI or WSGI implementation).

While early, this project is an attempt to achieve the following goals:

- Build an HTTP router based on radix trees.
- Make sure it shows good performance while looking-up HTTP paths (especially or in particular where there are _many, possible routes_ to select from).
- Provide implementations of routers for the ASGI spec.

As a secondary goal, a minimal web framework may in the future also be provided for building web applications in order to explore this space. However, more fully featured frameworks should be considered before this one. Producing a feature-complete web framework is _not_ a primary goal of this project.

## Is This Project Production Ready?

This is an experimental prototype, an exploration of radix routers in Python. It was first created in order to provide routing for a business project that grew to have many HTTP paths to choose from.

If you decide to test and then use this project in your projects, please let us know.

Caveat emptor!

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

Examples are provided in the [`./examples`](./examples/) directory. For instance, you can run an example application with `trio` and `hypercorn` like so:

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
