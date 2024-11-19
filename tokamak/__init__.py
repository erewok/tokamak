"""
Tokamak offers Radix Tree path routing and an experimental web framework.

Module Organization:

- ASGIRouter definition: [`tokamak.router`](../router)
- Radix Tree implementation: [`tokamak.radix_tree`](../radix_tree/__init__/)
- Experimental Web Framework: [`tokamak.web`](../web/__init__/)
"""

from .router import AsgiRouter, Route

__version__ = "0.5.5"
__all__ = ["AsgiRouter", "Route"]
