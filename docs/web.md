# Tokamak Experimental Web Framework

This library can be installed with the extra-feature "web" in order to use the experimental web framework.

This web framework is included as an optional install in this library for two reasons:

- It provides a convenient way to test the [`AsgiRouter`](/routing) class, and
- It allows this library to explore experimental ASGI-framework features, including request-cancellation, background task time-limits, and background task cancellation.

This page describes the `Tokamak` web application. Its behavior is highly limited compared to feature-complete web frameworks. For instance, it **does not** include the following features:

- Error handling
- Middleware

## `Tokamak` Application

::: tokamak.web.app.Tokamak
    members:
    - http
    - process_background
    - ws
    handler: python

## `Request` class

::: tokamak.web.request.Request

    members:
    - __init__
    - register_background
    - respond_with
    handler: python

## `Response` class

::: tokamak.web.response.Response

    members:
    - raw_headers
    handler: python
