"""
Tokamak offers Radix Tree path routing and an experimental web framework.

Module Organization:

- ASGIRouter definition: [`tokamak.router`](/reference/router)
- Radix Tree implementation: [`tokamak.radix_tree`](reference/radix_tree/__init__/)
- Experimental Web Framework: [`tokamak.web`](/reference/web/__init__/)
"""

__version__ = "0.5.3"
from .router import AsgiRouter, Route
