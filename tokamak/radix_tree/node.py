import copy
from collections.abc import MutableSet
from itertools import chain
from typing import (
    Any,
    Dict,
    Generic,
    Iterable,
    Iterator,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)

from . import utils

LAST_CHILD = "└──"
MIDDLE_CHILD = "├──"
BAR = "│  "
V = TypeVar("V")  # handler value


class PrefixSearchResult:
    __slots__ = [
        "node",
        "index",
        "left_side_remaining",
        "right_side_remaining",
    ]

    def __init__(
        self,
        node: "RadixNode",
        index: int,
        left_side_remaining: str,
        right_side_remaining: str,
    ):
        self.node = node
        self.index = index
        self.left_side_remaining = left_side_remaining
        self.right_side_remaining = right_side_remaining

    @property
    def complete_match(self) -> bool:
        return len(self.left_side_remaining) == 0 == len(self.right_side_remaining)

    def __str__(self) -> str:
        return "Path: {} Index: {} [Left: {} <//> Right: {}]".format(
            self.node.path,
            self.index,
            self.left_side_remaining,
            self.right_side_remaining,
        )


class LeafNode(Generic[V]):
    __slots__ = ["handler"]

    def __init__(self, handler: V):
        self.handler = handler


class NodeChildSet(MutableSet):
    """
    The goal of this data structure is to make it easy
    to iterate StaticNodes _before_ DynamicNodes.

    We keep two Sets below the surface: one for StaticNodes and one for DynamicNodes.
    Then, when iterating, we iterate StaticNodes first.
    """

    __slots__ = ["static_nodes", "dynamic_nodes"]

    def __init__(self, data: Optional[Iterable["RadixNode"]] = None):
        self.static_nodes: Set["RadixNode"] = set()
        self.dynamic_nodes: Set["RadixNode"] = set()

        if data is not None:
            for node in data:
                if isinstance(node, DynamicNode):
                    self.dynamic_nodes.add(node)
                else:
                    self.static_nodes.add(node)

    def add(self, node: "RadixNode") -> None:
        """
        Put item into appropriate set. If key already
        exists in the _other_ set, we delete it from there
        afterward.
        """
        if isinstance(node, DynamicNode):
            self.dynamic_nodes.add(node)
            if node in self.static_nodes:
                self.static_nodes.discard(node)
        else:
            self.static_nodes.add(node)
            if node in self.dynamic_nodes:
                self.dynamic_nodes.discard(node)

    def discard(self, node: "RadixNode") -> None:
        if node in self.dynamic_nodes:
            return self.dynamic_nodes.discard(node)
        return self.static_nodes.discard(node)

    # We are interested in specializing this data structure: only RadixNode things are allowed
    def __contains__(self, node: "RadixNode") -> bool:  # type: ignore
        return node in self.dynamic_nodes or node in self.static_nodes

    def __iter__(self) -> Iterator["RadixNode"]:
        return chain(self.static_nodes, self.dynamic_nodes)

    def __len__(self) -> int:
        return len(self.static_nodes) + len(self.dynamic_nodes)

    def __repr__(self) -> str:
        return "<tokamak.radix_tree.node.{classname}(.|S|. {static_nodes}) (.|D|. {dynamic_nodes})>".format(
            classname=type(self).__name__,
            static_nodes=repr(self.static_nodes),
            dynamic_nodes=repr(self.dynamic_nodes),
        )


class RadixNode(Generic[V]):
    __slots__ = ["path", "children", "leaf", "separator"]

    def __init__(
        self,
        path: str,
        children: Optional[NodeChildSet] = None,
        leaf: Optional["LeafNode[V]"] = None,
        separator: str = "/",
    ):
        self.path = path
        self.children: NodeChildSet = children or NodeChildSet()
        self.leaf = leaf
        self.separator = separator

    # needs structural typing?
    def __eq__(self, other_node) -> bool:  # type: ignore
        """
        Note: this equality checks _only_ the nodes. It does not recurse
        into child nodes, so the sub-trees may be different for nodes that are
        equal.
        """
        index = utils.first_nonequal_idx(self.path, other_node.path)
        if index == len(self.path) == len(other_node.path):
            return True
        return False

    def __hash__(self) -> int:
        return hash(self.path)

    def __str__(self) -> str:
        self_string = (
            "<tokamak.radix_tree.node.{cls} '{path}' "
            "with child count {childlen} at {lookup}>"
        )
        return self_string.format(
            cls=type(self).__name__,
            path=self.path,
            childlen=len(self.children),
            lookup=hex(id(self)),
        )

    def __repr__(self) -> str:
        return "<tokamak.radix_tree.node.{classname} '{path}' at {loc}>".format(
            classname=type(self).__name__, path=self.path, loc=hex(id(self))
        )

    def __len__(self) -> int:
        """Returns count of all nodes in the tree"""
        return 1 + sum(len(ch) for ch in self.children)

    def clone(self, path: Optional[str] = None) -> "RadixNode":  # type: ignore # pragma: no cover
        raise NotImplementedError("`clone` must be implemented in the child classes")

    def split(self, index: int) -> "RadixNode":  # type: ignore # pragma: no cover
        raise NotImplementedError("`split` must be implemented in the child classes")

    def insert_dynamic_node(
        self, node: "DynamicNode", psr: PrefixSearchResult
    ) -> "RadixNode":
        if not psr.complete_match:
            raise ValueError("Can't insert dynamic node without complete match")
        return merge_nodes(psr.node, node)

    def insert_static_node(
        self, node: "StaticNode", psr: PrefixSearchResult
    ) -> "RadixNode":
        if psr.complete_match:
            return merge_nodes(psr.node, node)
        elif psr.left_side_remaining:
            psr.node.split(psr.index)
            if psr.right_side_remaining:
                node.path = psr.right_side_remaining
                psr.node.children.add(node)
                return node
            else:
                return merge_nodes(psr.node, node)
        else:
            node.path = psr.right_side_remaining
            psr.node.children.add(node)
            return node

    def insert_node(self, node: "RadixNode") -> "RadixNode":
        if not self.children and len(self.path) == 0:
            self.children.add(node)
            return node
        # we compare paths directly here because no children (instead of prefix search)
        elif not self.children and self.path == node.path:
            if self.leaf and node.leaf:
                msg = "Merge conflict: duplicate nodes both have handler for path '{}'"
                raise ValueError(msg.format(self.path))
            elif not self.leaf and node.leaf:
                self.leaf = node.leaf
            self.children = node.children
            return self
        elif not self.children:
            self.children.add(node)
            return node

        try:
            psr = next(self.prefix_search(node.path))
        except StopIteration:
            raise ValueError("Failed inserting node with path: {}".format(node.path))

        if isinstance(node, DynamicNode):
            result = self.insert_dynamic_node(node, psr)
        elif isinstance(node, StaticNode):
            result = self.insert_static_node(node, psr)
        else:
            raise ValueError("Unknown nodetype: ", node.__class__)

        return result

    def insert(self, path: str, handler: Optional[V] = None) -> Optional["RadixNode"]:
        """
        Inserts a path somewhere in this tree as a new subtree

        May include dynamic path parts.
        """
        # create a new tree out of this path and insert the node
        new_path_root = path_to_tree(path, handler)
        return self.insert_node(new_path_root)

    def prefix_search(
        self,
        prefix: str,
    ) -> Iterator[PrefixSearchResult]:
        """
        Searches a prefix and yields all nodes that match.

        We yield inside-out, so the deepest matching node should appear first in results.

        Note: this method doesn't guarantee a full match. It means only that
        there are _some_ matching characters for this prefix.
        """
        for child in self.children:
            yield from child.prefix_search(prefix)

        # this node always "matches"
        yield PrefixSearchResult(self, len(self.path), "", "")

    def prettyprint(self, mult: int = 1, indent: str = "") -> None:  # pragma: no cover
        result = self.tree_as_str(mult=mult, indent=indent)
        print(result)
        return None

    def search_path(
        self,
        path: str,
        context: Optional[Dict[str, str]] = None,
    ) -> Tuple[Optional["RadixNode"], Dict[str, str]]:
        """
        Searches for a prefix and returns only a node that is a _complete_ match.
        """
        matched_vars: Dict[str, str] = {}
        if context is not None:
            matched_vars = context

        index = utils.first_nonequal_idx(path, self.path)
        if index == len(self.path) == len(path):
            return self, matched_vars

        if len(self.path) == 0 or (index == len(self.path) and index < len(path)):
            for child in self.children:
                matched_node, matched_vars = child.search_path(
                    path[index:], context=matched_vars
                )
                if matched_node:
                    return matched_node, matched_vars

        return None, matched_vars

    def tree_as_str(
        self, mult: int = 1, indent: str = "", is_leaf: bool = False
    ) -> str:
        visual = "{indent}{branch} {path}\n"
        path = self.path
        if not path:
            path = "* <-root->"
        elif self.leaf is not None:
            path += " <*>"

        result = ""
        if is_leaf or not path:  # "not indent" means top-level
            result += visual.format(indent=indent, branch=LAST_CHILD, path=path)
        else:
            result += visual.format(indent=indent, branch=MIDDLE_CHILD, path=path)
        mult += 1
        indent += " " * mult
        for idx, ch in enumerate(self.children):
            is_leaf = idx == len(self.children) - 1
            result += ch.tree_as_str(indent=indent, mult=mult, is_leaf=is_leaf)
        return result


class StaticNode(RadixNode):
    def __init__(
        self,
        path: str,
        children: Optional[NodeChildSet] = None,
        leaf: Optional[LeafNode] = None,
        separator: str = "/",
    ):
        if not path:
            raise ValueError("StaticNode constructor called with an empty `path`")

        self.path = path
        self.children: NodeChildSet = children or NodeChildSet()
        self.leaf = leaf
        self.separator = separator

    def clone(self, path: Optional[str] = None) -> "RadixNode":
        if path is None:
            path = self.path

        children = copy.deepcopy(self.children)
        new_node = StaticNode(
            path,
            children=children,
            leaf=self.leaf,
            separator=self.separator,
        )
        return new_node

    def split(self, idx: int) -> "RadixNode":
        path_split_prefix = self.path[:idx]
        path_split_suffix = self.path[idx:]
        new_node = self.clone(path=path_split_suffix)

        self.path = path_split_prefix
        self.children = NodeChildSet((new_node,))
        if self.leaf is not None:
            self.leaf = None
        return self

    def prefix_search(
        self,
        prefix: str,
    ) -> Iterator[PrefixSearchResult]:
        """
        Searches a prefix and yields all nodes that match.

        We yield inside-out, so the deepest matching node should appear first in results.

        Note: this method doesn't guarantee a full match. It means only that
        there are _some_ matching characters for this prefix.

        Check the PrefixSearchResult object for unmatched characters.
        """
        index = utils.first_nonequal_idx(prefix, self.path)
        if index == len(self.path) == len(prefix):
            # full match; prefix fully consumed
            yield PrefixSearchResult(self, index, "", "")
        elif index > 0 and index == len(self.path):
            # this node matched: check children for remaining
            remaining = prefix[index:]
            for child in self.children:
                yield from child.prefix_search(remaining)

            yield PrefixSearchResult(self, index, "", remaining)
        elif index > 0:
            # partial match
            unmatched = self.path[index:]
            remaining = prefix[index:]
            yield PrefixSearchResult(self, index, unmatched, remaining)

    def search_path(
        self,
        path: str,
        context: Optional[Dict[str, str]] = None,
    ) -> Tuple[Optional["RadixNode"], Dict[str, str]]:
        """
        Searches for a prefix and returns only a node that is a _complete_ match.

        For dynamic nodes, it will use the regex parser to match the input `path`.

        We yield inside-out, so the deepest matching node should appear first in results.

        Note: this method doesn't guarantee a full match. It means only that
        there are _some_ matching characters for this prefix.
        """
        matched_vars: Dict[str, str] = {}
        if context is not None:
            matched_vars = context

        index = utils.first_nonequal_idx(path, self.path)
        if index == len(self.path) == len(path):
            return self, matched_vars

        if index == len(self.path) and index < len(path):
            for child in self.children:
                matched_node, matched_vars = child.search_path(
                    path[index:], context=matched_vars
                )
                if matched_node:
                    return matched_node, matched_vars

        return None, matched_vars


class DynamicNode(RadixNode):
    __slots__ = ["parser", "children", "leaf", "separator"]

    def __init__(
        self,
        parser: utils.DynamicParseNode,
        children: Optional[NodeChildSet] = None,
        leaf: Optional[LeafNode] = None,
        separator: str = "/",
    ):
        self.path = parser.raw
        self.parser = parser
        self.children = children or NodeChildSet()
        self.leaf = leaf
        self.separator = separator

    def clone(self, **kwargs) -> "RadixNode":  # type: ignore
        children = copy.deepcopy(self.children)
        new_node = DynamicNode(
            self.parser, children=children, leaf=self.leaf, separator=self.separator
        )
        return new_node

    def prefix_search(self, prefix: str) -> Iterator[PrefixSearchResult]:
        """
        Searches a prefix and yields all nodes that match.

        We yield inside-out, so the deepest matching node should appear first in results.

        Check the PrefixSearchResult object for unmatched characters.

        Note: When inserting dynamic nodes, we need some way to check that they're the same.

        This is different from searching an input string using the regex. We look for a completely
        matching dynamic path.
        """
        index = utils.first_nonequal_idx(prefix, self.path)
        if index == len(self.path) == len(prefix):
            # full match; prefix fully consumed
            yield PrefixSearchResult(self, index, "", "")

        # we proceed only if the raw path is completely consumed
        if index == len(self.path) and len(prefix) > len(self.path):
            unmatched = self.path[:index]
            remaining = prefix[index:]

            for child in self.children:
                yield from child.prefix_search(remaining)

            yield PrefixSearchResult(self, index, unmatched, remaining)

    def search_path(
        self, path: str, context: Optional[Dict[str, str]] = None
    ) -> Tuple[Optional["RadixNode"], Dict[str, str]]:
        matched_vars: Dict[str, str] = {}
        if context is not None:
            matched_vars = context

        end_idx, matched = self.parser.match(path)
        if matched:
            matched_vars.update(matched)

        if matched and end_idx == len(path):
            return self, matched_vars

        if matched and end_idx < len(path):
            for child in self.children:
                matched_node, matched_vars = child.search_path(
                    path[end_idx:], context=matched_vars
                )
                if matched_node:
                    return matched_node, matched_vars

        return None, matched_vars


# # # # # # # # # # # # # # # # # # # #
# #
# Helpers
# #
# # # # # # # # # # # # # # # # # # # #
def node_map(
    element: Union[utils.DynamicParseNode, str]
) -> Union[DynamicNode, StaticNode]:
    """
    Returns a `DynamicNode` or a `StaticNode` for any `str` or parser passed in.
    """
    if isinstance(element, utils.DynamicParseNode):
        return DynamicNode(element)
    elif isinstance(element, str):
        return StaticNode(element)
    raise ValueError("Uknown type for node mapping")


def path_to_tree(path: str, handler: Any) -> RadixNode:
    """
    Create a _new_ tree out of this path. Because this is a new node, it
    should contain only simple `parent.children = {child-node}` relationships.

    Returns root node.
    """
    path_nodes = list(enumerate(map(node_map, utils.parse_dynamic(path))))
    if len(path_nodes) == 0:
        raise ValueError("`path_to_tree` called with inscrutable path")

    new_path_root = path_nodes[0][1]
    if len(path_nodes) == 1 and handler is not None:
        new_path_root.leaf = LeafNode(handler=handler)
    else:
        last_node_idx = len(path_nodes) - 1
        latest_root: RadixNode = new_path_root
        for idx, node in path_nodes[1:]:
            if handler is not None and idx == last_node_idx:
                node.leaf = LeafNode(handler=handler)
            latest_root = latest_root.insert_node(node)

    return new_path_root


def merge_nodes(into: RadixNode, merge_node: RadixNode) -> RadixNode:
    if (
        into.leaf is not None
        and merge_node.leaf is not None
        and into.leaf != merge_node.leaf
    ):
        msg = "Merge conflict: duplicate nodes both have handler for path '{}'"
        raise ValueError(msg.format(into.path))

    if into.leaf is None and merge_node.leaf is not None:
        into.leaf = merge_node.leaf

    if not merge_node.children:
        return into

    if into.children.isdisjoint(merge_node.children):
        new_children = into.children | merge_node.children
        into.children = NodeChildSet(new_children)
        return into

    # Poor performance: look for algo for merging radix trees
    # On the plus: if `prefix_search` is accurate, then our insertion point
    # is lowest possible point on the tree.
    shared = into.children & merge_node.children
    into_child_shared = {nd.path: nd for nd in into.children if nd in shared}
    merge_child_shared = {nd.path: nd for nd in merge_node.children if nd in shared}

    different_children = (into.children | merge_node.children) - shared
    into.children = NodeChildSet(different_children)

    for nd in shared:
        new_into = into_child_shared[nd.path]
        new_merge = merge_child_shared[nd.path]
        into.children.add(merge_nodes(new_into, new_merge))

    return into
