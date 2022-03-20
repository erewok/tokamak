import enum
from typing import Optional

SCOPE_METHOD_KEY = "method"


@enum.unique
class Method(enum.Enum):
    CONNECT = "CONNECT"
    DELETE = "DELETE"
    HEAD = "HEAD"
    GET = "GET"
    OPTIONS = "OPTIONS"
    PATCH = "PATCH"
    POST = "POST"
    PUT = "PUT"
    TRACE = "TRACE"

    @classmethod
    def read(cls, value: str) -> Optional["Method"]:
        if hasattr(value, "upper"):
            value = value.upper()
        for elem in Method:
            if elem.value == value:
                return elem
        return None
