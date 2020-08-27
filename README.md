# Tokamak

> In a star as in a fusion device, plasmas provide the environment in which light elements can fuse and yield energy.

Tokamak is a router based on Radix trees intended for ASGI Python applications.

## Project Goals (Why Did You Build This?)

This project was created to fill a gap in the Python ecosystem. In various other language communities, including Go, Javascript, and others, HTTP routers based on radix trees have been provided by open-source projects. In Python, no such library exists and most open-source Python web frameworks utilize lists to store and look up HTTP routes.

Thus, this project exists to provide radix-tree-based router for Python web frameworks (or any custom ASGI or WSGI implementation).

While early, this project is an attempt to achieve the following goals:

- Build an HTTP router based on radix trees.
- Make sure it shows good performance well while looking-up HTTP paths (especially or in particular where there are _many, possible routes_ to select from).
- Provide implementations of routers for the ASGI spec (and possibly the WSGI spec as well).

As a secondary goal, a minimal web framework may in the future also be provided for building web applications, but more fully featured frameworks should be considered before this one. Producing a feature-complete web framework is _not_ a primary goal of this project.

## Is This Project Production Ready

This is an experimental prototype, untested in the wild. It was first created in order to provide routing for a project that grew to have many HTTP paths to choose from.

If you decide to test and then use this project in your projects, please let us know.

Caveat emptor!


## Installation

You can install `tokamak` with:

```sh
$ pip install tokamak
```

Tokamak has no dependencies.

## Usage

TODO
