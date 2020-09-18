import random
import typing

import pytest

from tokamak.radix_tree import Tree, node, utils

SimpleTree = typing.Tuple[
    node.StaticNode, node.StaticNode, node.StaticNode, node.StaticNode
]


@pytest.fixture()
def static_node() -> node.RadixNode:
    return node.StaticNode(
        "/a/b/c/d/e", children=node.NodeChildSet({node.StaticNode("f")})
    )


@pytest.fixture()
def dynamic_node() -> node.RadixNode:
    return node.DynamicNode(
        utils.DynamicParseNode(
            "{name:[a-zA-Z][0-9]{2}[a-zA-Z0-9]*}",
            "name",
            regex="[a-zA-Z][0-9]{2}[a-zA-Z0-9]*",
        )
    )


@pytest.fixture()
def simple_tree() -> SimpleTree:
    root = node.StaticNode("/")
    co_parent = node.StaticNode("co")
    comp_parent = node.StaticNode("m")
    pany_parent = node.StaticNode("pany")
    root.children = node.NodeChildSet((co_parent,))

    co_parent.children = node.NodeChildSet((node.StaticNode("ntact"), comp_parent))
    comp_parent.children = node.NodeChildSet((pany_parent, node.StaticNode("e"),))
    return root, co_parent, comp_parent, pany_parent


# # # # # # # # # # # # # # # # # # # #
# #
# PrefixSearchResult
# #
# # # # # # # # # # # # # # # # # # # #
def test_prefix_search_result() -> None:
    psr = node.PrefixSearchResult(node.StaticNode("path!"), 1, "", "")
    assert psr.complete_match

    assert "path!" in str(psr)
    assert "1" in str(psr)

    psr = node.PrefixSearchResult(node.StaticNode("path!"), 1, "a", "b")
    assert not psr.complete_match
    assert "path!" in str(psr)
    assert "1" in str(psr)
    assert "a" in str(psr)
    assert "b" in str(psr)


# # # # # # # # # # # # # # # # # # # #
# #
# NodeChildSet
# #
# # # # # # # # # # # # # # # # # # # #
@pytest.fixture()
def some_nodes(dynamic_node: node.RadixNode) -> typing.List[node.RadixNode]:
    nodes = [
        dynamic_node,
        node.DynamicNode(utils.DynamicParseNode("{test}", "test", regex=None,)),
        node.StaticNode("/a"),
        node.StaticNode("/b"),
    ]
    return nodes


def test_childset_ctor(some_nodes: typing.List[node.RadixNode]) -> None:
    random.shuffle(some_nodes)
    childset = node.NodeChildSet(some_nodes)
    assert len(childset.static_nodes) == 2
    assert len(childset.dynamic_nodes) == 2


def test_childset_add(some_nodes: typing.List[node.RadixNode]) -> None:
    childset = node.NodeChildSet(some_nodes)
    # We will make some unlikely nodes here in order to test the swap
    childset.add(node.StaticNode("{test}"))
    assert len(childset.static_nodes) == 3
    assert len(childset.dynamic_nodes) == 1
    assert len(childset) == 4
    childset.add(node.DynamicNode(utils.DynamicParseNode("/b", "test", regex=None)))
    assert len(childset.static_nodes) == 2
    assert len(childset.dynamic_nodes) == 2
    assert len(childset) == 4


def test_childset_discard(some_nodes: typing.List[node.RadixNode]) -> None:
    childset = node.NodeChildSet(some_nodes)
    childset.discard(some_nodes[1])
    assert len(childset.dynamic_nodes) == 1
    assert next(iter(childset.dynamic_nodes)) == some_nodes[0]

    childset.discard(some_nodes[-1])
    assert len(childset.static_nodes) == 1
    assert next(iter(childset.static_nodes)) == some_nodes[2]

    assert len(childset) == 2


def test_various_dunder(some_nodes: typing.List[node.RadixNode]) -> None:
    childset = node.NodeChildSet(some_nodes)
    child_list = list(childset)
    for item in child_list[:2]:
        assert isinstance(item, node.StaticNode)
    for item in child_list[2:]:
        assert isinstance(item, node.DynamicNode)

    for item in some_nodes:
        assert item in childset

    assert len(childset) == len(some_nodes)
    assert "<tokamak.radix_tree.node.NodeChildSet(" in repr(childset)


# # # # # # # # # # # # # # # # # # # #
# #
# RadixNode
# #
# # # # # # # # # # # # # # # # # # # #
def test_radix_node_dunder(static_node: node.StaticNode) -> None:
    sn2 = node.StaticNode(
        static_node.path,
        children=node.NodeChildSet({node.StaticNode("now")}),
        separator="::",
    )
    sn3 = node.StaticNode("another_path", children=None, separator=";",)
    # for now we compare _only_ paths
    assert static_node == sn2
    assert static_node != sn3

    assert hash(static_node) == hash(static_node.path)
    as_str = str(static_node)
    assert "StaticNode" in as_str
    assert static_node.path in as_str
    assert "0" in as_str

    as_repr = repr(static_node)
    assert "'{}'".format(static_node.path) in as_repr

    assert len(static_node) == 2
    assert len(sn3) == 1


def test_insert_dynamic_node(dynamic_node: node.DynamicNode) -> None:
    dyn_node = node.DynamicNode(
        utils.DynamicParseNode(
            "{name:[a-zA-Z][0-9]{2}[a-zA-Z0-9]*}",
            "name",
            regex="[a-zA-Z][0-9]{2}[a-zA-Z0-9]*",
        )
    )
    complete_psr = node.PrefixSearchResult(dyn_node, 5, "", "")
    assert dyn_node.insert_dynamic_node(dynamic_node, complete_psr) is dyn_node

    incomplete_psr = node.PrefixSearchResult(dynamic_node, 5, "left", "right")
    with pytest.raises(ValueError):
        dyn_node.insert_dynamic_node(dynamic_node, incomplete_psr)


@pytest.mark.parametrize(
    "path,has_handler,node_path",
    (
        ("/", True, "/"),
        ("/c", True, "c"),
        ("/a/b/c/d/e/f/g/h", True, "/g/h"),
        ("/contact", True, "ntact"),
        ("/doc", True, "oc"),
        ("/doc/code_faq.html", True, "_faq.html"),
        ("/doc/code1.html", True, "1.html"),
        ("/darüber/schloß", True, "arüber/schloß"),
        ("/darüber/schloß/ritter", True, "/ritter"),
        ("/hello/test", True, "test"),
        ("/search", True, "earch"),
        ("/a", False, None),
        ("/ab", False, None),
        ("/hi", False, None),
        ("/con", False, None),
        ("/cona", False, None),
        ("/no", False, None),
        ("/hello/test/bye", False, None),
    ),
)
def test_large_tree_search_path_static_paths(
    path: str, has_handler: bool, node_path: str, large_tree: Tree
) -> None:
    found_node, ctx = large_tree._root.search_path(path)
    if has_handler:
        msg = "Expected handler for path {}".format(path)
        assert found_node is not None and found_node.leaf is not None, msg
        assert found_node.path == node_path, "Path should be {}, not {}".format(
            found_node.path, path
        )
        assert found_node.leaf.handler is not None
        assert not ctx
    else:
        assert (
            found_node is None or found_node.leaf is None
        ), "Expected no handler for path {}".format(path)


@pytest.mark.parametrize(
    "path,has_handler,node_path,params",
    (
        ("/", True, "/", {}),
        ("/cmd/test", True, "{tool}", {"tool": "test"}),
        ("/cmd/test/3", True, "{sub}", {"tool": "test", "sub": "3"}),
        ("/dcb/test", True, "{tool}", {"tool": "test"}),
        ("/dcb/test/3", True, "{sub}", {"tool": "test", "sub": "3"}),
        ("/src/", False, "", {}),
        ("/src/some/file.png", False, "", {"filepath": "some"},),
        ("/search", True, "earch", {}),
        (
            "/search/someth!ng+in+ünìcodé",
            True,
            "{query}",
            {"query": "someth!ng+in+ünìcodé"},
        ),
        ("/user_erik", True, "{name}", {"name": "erik"}),
        ("/user_erik/dept", True, "/dept", {"name": "erik"}),
        (
            "/files/js/framework.js",
            True,
            "{filepath:*}",
            {"dir": "js", "filepath": "framework.js"},
        ),
        ("/files/js/inc/framework.js", False, "", {"dir": "js", "filepath": "inc"},),
        ("/info", False, "", {}),
        ("/info/erik", True, "{user}", {"user": "erik"}),
        ("/info/erik/project", True, "/project", {"user": "erik"}),
        (
            "/info/erik/project/tokamak",
            True,
            "{project}",
            {"user": "erik", "project": "tokamak"},
        ),
    ),
)
def test_large_tree_search_path_dynamic_paths(  # type: ignore
    path, has_handler, node_path, params, large_tree
):
    found_node, ctx = large_tree._root.search_path(path)
    if has_handler:
        msg = "Expected handler for path {}".format(path)
        assert found_node is not None and found_node.leaf is not None, msg
        assert found_node.path == node_path, "Path should be {}, not {}".format(
            found_node.path, path
        )
        assert found_node.leaf.handler is not None
        assert params == ctx
    else:
        assert (
            found_node is None or found_node.leaf is None
        ), "Expected no handler for path {}".format(path)


def test_radix_tree_prefix_search_static(simple_tree: SimpleTree) -> None:
    root, co_parent, _, pany_parent = simple_tree
    result = list(root.prefix_search("/company"))
    assert len(result) == 4
    assert result[0].node is pany_parent

    partialresult = list(root.prefix_search("/clouds"))
    assert len(partialresult) == 2
    assert partialresult[0].node is co_parent

    noresult = list(root.prefix_search("not_present"))
    assert len(noresult) == 0


def test_radix_tree_prefix_search_dynamic(
    simple_tree: SimpleTree, dynamic_node: node.RadixNode
) -> None:
    root, co_parent, comp_parent, pany_parent = simple_tree
    pattern = "{name:[a-zA-Z][0-9]{2}[a-zA-Z0-9]*}"
    new_slash_node = pany_parent.insert_node(node.StaticNode("/"))
    new_slash_node.insert_node(dynamic_node)

    result = list(root.prefix_search("/company/{}".format(pattern)))
    assert len(result) == 6
    assert result[0].node is dynamic_node
    assert result[1].node is new_slash_node
    assert result[2].node is pany_parent
    assert result[3].node is comp_parent
    assert result[4].node is co_parent
    assert result[5].node is root


def test_radix_tree_search_path_dynamic(
    simple_tree: SimpleTree, dynamic_node: node.RadixNode
) -> None:
    root, _, _, pany_parent = simple_tree
    new_slash_node = pany_parent.insert_node(node.StaticNode("/"))
    new_slash_node.insert_node(dynamic_node)
    found_node, context = root.search_path("/company/a01a3a4")

    assert found_node is dynamic_node
    assert context == {"name": "a01a3a4"}

    no_result, no_context = root.search_path("/company/__**__")
    assert no_result is None
    assert not no_context


@pytest.mark.parametrize(
    "path,parent_paths",
    (
        ("/", ["/", ""]),
        ("/zzzz", ["/", ""]),
        ("/a/b/c/d/e/f/g/h/i/j", ["/g/h", "f", "a/b/c/d/e/", "/", ""]),
        (
            "/files/{dir}/{filepath:*}",
            ["{filepath:*}", "/", "{dir}", "files/", "/", ""],
        ),
        ("/cmd/{tool}/{sub}", ["{sub}", "/", "{tool}", "md/", "c", "/", ""]),
    ),
)
def test_radix_tree_prefix_search_large(
    path: str, parent_paths: typing.List[str], large_tree: Tree
) -> None:
    expected_answer_iter = zip(parent_paths, large_tree._root.prefix_search(path))
    for expected, psr in expected_answer_iter:
        assert expected == psr.node.path


def test_tree_as_str(large_tree: Tree) -> None:
    result = large_tree._root.tree_as_str()
    assert result.startswith("├── * <-root->")
    nested_childrens = (
        # cannot guarantee which of these will be last child
        "── a/b/c/d/e/\n",
        "             └── /g/h <*>\n",
        "── g <*>\n",
        "── f <*>\n ",
        "── h <*>\n",
    )
    for child in nested_childrens:
        assert child in result


# # # # # # # # # # # # # # # # # # # #
# #
# Test StaticNode
# #
# # # # # # # # # # # # # # # # # # # #
def test_static_node_init_and_clone(static_node: node.StaticNode) -> None:
    with pytest.raises(ValueError):
        node.StaticNode("")
    sn1 = node.StaticNode(
        "//bla", leaf=node.LeafNode("Handle"), children=node.NodeChildSet([static_node])
    )
    cloned_sn1 = sn1.clone()
    assert cloned_sn1.children == sn1.children
    assert cloned_sn1.path == sn1.path
    assert cloned_sn1.leaf == sn1.leaf


def test_static_node_split(static_node: node.StaticNode) -> None:
    cached_path = static_node.path
    static_node.leaf = node.LeafNode("A")
    assert static_node.split(2) is static_node
    assert static_node.path == cached_path[:2]
    assert len(static_node.children) == 1
    first_child = next(iter(static_node.children))
    assert first_child.path == cached_path[2:]
    assert static_node.leaf is None
    assert first_child.leaf is not None and first_child.leaf.handler == "A"


# # # # # # # # # # # # # # # # # # # #
# #
# Test DynamicNode
# #
# # # # # # # # # # # # # # # # # # # #


# # # # # # # # # # # # # # # # # # # #
# #
# Test Helpers
# #
# # # # # # # # # # # # # # # # # # # #
@pytest.mark.parametrize(
    "element,result",
    (
        (
            utils.DynamicParseNode(
                "{name:[a-zA-Z][0-9]{2}[a-zA-Z0-9]*}",
                "name",
                regex="[a-zA-Z][0-9]{2}[a-zA-Z0-9]*",
            ),
            node.DynamicNode,
        ),
        ("some_str", node.StaticNode),
        (None, ValueError),
        (set(), ValueError),
        (b"", ValueError),
    ),
)
def test_node_map(element, result):  # type: ignore
    if result == ValueError:
        with pytest.raises(result):
            node.node_map(element)
    else:
        assert isinstance(node.node_map(element), result)


@pytest.mark.parametrize(
    "path,query,leaf_path,tree_depth",
    (
        ("", None, None, 0),
        ("/hello", "/hello", "/hello", 1),
        ("/hello/{world}", "/hello/world", "{world}", 2),
        ("/hello/{world}/{earth}", "/hello/world/stars", "{earth}", 4),
        ("/hello/{world:[a-zA-Z]+};{test}", "/hello/world;earth", "{test}", 4),
        (
            "/{variable:[a-zA-Z]+}-{world:[a-zA-Z]+}-{test:[a-zA-Z]+}",
            "/hello-world-earth",
            "{test:[a-zA-Z]+}",
            6,
        ),
        (
            "{variable:[a-zA-Z]+}-{world:[a-zA-Z]+}-{test:[a-zA-Z]+}",
            "hello-world-earth",
            "{test:[a-zA-Z]+}",
            5,
        ),
    ),
)
def test_path_to_tree(path: str, query: str, leaf_path: str, tree_depth: int) -> None:
    if tree_depth == 0:
        with pytest.raises(ValueError):
            new_node = node.path_to_tree(path, "A")
    else:
        new_node = node.path_to_tree(path, "A")
        assert len(new_node) == tree_depth
        leaf, _ = new_node.search_path(query)
        assert leaf is not None
        assert leaf.leaf is not None
        assert leaf.path == leaf_path
        assert leaf.leaf.handler == "A"


@pytest.mark.parametrize(
    "into_path,merge_node_path,handlers",
    (
        (
            (
                "/",
                "/",
                {"left": "LEFT", "right": "RIGHT", "result": None, "error": True},
            ),
            (
                "/",
                "/",
                {"left": "LEFT", "right": None, "result": "LEFT", "error": False},
            ),
            (
                "/",
                "/",
                {"left": None, "right": "RIGHT", "result": "RIGHT", "error": False},
            ),
        )
    ),
)
def test_merge_nodes(into_path: str, merge_node_path: str, handlers: dict) -> None:
    into = node.path_to_tree(into_path, handlers["left"])
    merge_node = node.path_to_tree(merge_node_path, handlers["right"])
    if handlers["error"]:
        with pytest.raises(ValueError):
            node.merge_nodes(into, merge_node)
    else:
        result = node.merge_nodes(into, merge_node)
        assert result is into
        if handlers["result"]:
            assert result.leaf is not None and result.leaf.handler == handlers["result"]
