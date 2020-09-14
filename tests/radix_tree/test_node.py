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
def simple_tree() -> SimpleTree:
    root = node.StaticNode("/")
    co_parent = node.StaticNode("co")
    comp_parent = node.StaticNode("m")
    pany_parent = node.StaticNode("pany")
    root.children = node.NodeChildSet((co_parent,))

    co_parent.children = node.NodeChildSet((node.StaticNode("ntact"), comp_parent))
    comp_parent.children = node.NodeChildSet(
        (
            pany_parent,
            node.StaticNode("e"),
        )
    )
    return root, co_parent, comp_parent, pany_parent


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


def test_radix_node_dunder(static_node: node.RadixNode) -> None:
    sn2 = node.StaticNode(
        static_node.path,
        children=node.NodeChildSet({"hey": node.StaticNode("now")}),
        separator="::",
    )
    # for now we compare _only_ paths
    assert static_node == sn2

    assert hash(static_node) == hash(static_node.path)
    as_str = str(static_node)
    assert "StaticNode" in as_str
    assert static_node.path in as_str
    assert "0" in as_str


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
def test_large_tree_search_path_static(
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
        (
            "/src/some/file.png",
            False,
            "",
            {"filepath": "some"},
        ),
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
        (
            "/files/js/inc/framework.js",
            False,
            "",
            {"dir": "js", "filepath": "inc"},
        ),
        ("/info/erik/public", True, "/public", {"user": "erik"}),
        (
            "/info/erik/project/tokamak",
            True,
            "{project}",
            {"user": "erik", "project": "tokamak"},
        ),
        ("/info/erik", False, "", {}),
    ),
)
def test_large_tree_search_path_dyanmic_paths(
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


def test_radix_tree_prefix_search_dynamic(simple_tree: SimpleTree) -> None:
    root, co_parent, comp_parent, pany_parent = simple_tree
    pattern = "{name:[a-zA-Z][0-9]{2}[a-zA-Z0-9]*}"
    dyn_node = node.DynamicNode(
        utils.DynamicParseNode(
            pattern,
            "name",
            regex=pattern[6:-1],
        )
    )
    new_slash_node = pany_parent.insert_node(node.StaticNode("/"))
    new_slash_node.insert_node(dyn_node)

    result = list(root.prefix_search("/company/{}".format(pattern)))
    assert len(result) == 6
    assert result[0].node is dyn_node
    assert result[1].node is new_slash_node
    assert result[2].node is pany_parent
    assert result[3].node is comp_parent
    assert result[4].node is co_parent
    assert result[5].node is root


def test_radix_tree_search_path_dynamic(simple_tree: SimpleTree) -> None:
    root, _, comp_parent, pany_parent = simple_tree
    dyn_node = node.DynamicNode(
        utils.DynamicParseNode(
            "{name:[a-zA-Z][0-9]{2}[a-zA-Z0-9]*}",
            "name",
            regex="[a-zA-Z][0-9]{2}[a-zA-Z0-9]*",
        )
    )
    new_slash_node = pany_parent.insert_node(node.StaticNode("/"))
    new_slash_node.insert_node(dyn_node)
    found_node, context = root.search_path("/company/a01a3a4")

    assert found_node is dyn_node
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
