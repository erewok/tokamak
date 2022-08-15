"""
These modules encompass the experimental Tokamak web framework.

To install this library with this module available, the "web" optional
extra must be included, e.g.:

    $ pip install "tokamak[web]"

Module Organization:

- Tokamak Applications: [`tokamak.web.app`](../app/)
- Request Class: [`tokamak.web.request`](../request/)
- Response Class: [`tokamak.web.response`](../response/)
"""
from .app import Tokamak
from .request import Request
from .response import Response
