import enum
from typing import Any, Dict, Tuple

from . import node


class TrailingSlashMatch(enum.Enum):
    STRICT = 1
    RELAXED = 2


class Tree:
    def __init__(
        self,
        separator: str = "/",
        default_handler: Any = None,
        trailing_slash_match: TrailingSlashMatch = TrailingSlashMatch.RELAXED,
    ):
        if default_handler is not None:
            self._root: node.RadixNode = node.RadixNode(
                "", separator=separator, leaf=node.LeafNode(default_handler)
            )
        else:
            self._root = node.RadixNode("", separator=separator)

        self.separator = separator
        self.trailing_slash_match = trailing_slash_match

    def insert(self, path: str, handler: Any) -> None:
        if not path.startswith(self.separator):
            raise ValueError("Path must start with '{}'".format(self.separator))

        if (
            self.trailing_slash_match is TrailingSlashMatch.RELAXED
            and len(path) > 1
            and path[-1] == self.separator
        ):
            path = path[:-1]
        self._root.insert(path, handler)

    def get_handler(self, path: str) -> Tuple[Any, Dict[str, str]]:
        if (
            self.trailing_slash_match is TrailingSlashMatch.RELAXED
            and len(path) > 1
            and path[-1] == self.separator
        ):
            path = path[:-1]

        context: Dict[str, str] = {}
        result, context = self._root.search_path(path, context=context)
        if result and result.leaf and result.leaf.handler:
            return result.leaf.handler, context
        if self._root.leaf is not None:
            return self._root.leaf.handler, context
        return None, context

    def prettyprint(self) -> None:  # pragma: no cover
        return self._root.prettyprint()
