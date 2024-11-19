import pytest
from tokamak.radix_tree import utils


def test_dyn_parse_node_init():
    with pytest.raises(ValueError):
        utils.DynamicParseNode("raw", "09ab")
    with pytest.raises(ValueError):
        utils.DynamicParseNode("raw", "")
    dyn = utils.DynamicParseNode("raw", "ab01", regex="[0-9]+")
    assert dyn.regex == "[0-9]+"
    dyn = utils.DynamicParseNode("raw", "ab01", regex=None)
    assert dyn.regex == utils.DynamicParseNode.MATCH_UP_TO_SLASH

    dyn = utils.DynamicParseNode("raw", "ab01", regex="*")
    assert dyn.regex == utils.DynamicParseNode.MATCH_UP_TO_SLASH


def test_dyn_parse_node_pattern():
    dyn_noregex = utils.DynamicParseNode("raw", "ab01", regex=None)
    assert dyn_noregex.pattern is not None

    dyn = utils.DynamicParseNode("raw", "ab01", regex="[0-9]+")
    assert dyn._pattern is None
    assert dyn.pattern is not None
    assert dyn._pattern is not None
    assert dyn._pattern == dyn.pattern


@pytest.mark.parametrize(
    "test_val,should_match,start,end",
    (
        ("0000AABB34xxxx---/", True, 0, 10),
        ("xxxx---/0000AABB34xxxx---/", False, None, None),  # `match` only matches start
    ),
)
def test_dyn_parse_node_match(test_val, should_match, start, end):
    dyn = utils.DynamicParseNode(
        "{name:[0-2]+AABB[3-4]{2}}", "name", regex="[0-2]+AABB[3-4]{2}"
    )
    result = dyn.match(test_val)
    if not should_match:
        assert result == (-1, None)
    else:
        assert result[0] == end
        assert result[1]["name"] == test_val[start:end]


# TODO: Add hypothesis
@pytest.mark.parametrize(
    "val,expected",
    (
        (("ab", "ab"), 2),
        (("aba", "abc"), 2),
        (("", "california"), 0),
        (("california", ""), 0),
        (("", ""), 0),
    ),
)
def test_first_nonequal_idx(val, expected):
    assert utils.first_nonequal_idx(*val) == expected


@pytest.mark.parametrize(
    "test_val,expected",
    (
        ("/first/second/third", "/first/second/third"),
        ("/first/ /third", "/first/ /third"),
        ("/first/schloß/third", "/first/schloß/third"),
    ),
)
def test_parse_dyn_boring_input(test_val, expected):
    assert next(utils.parse_dynamic(test_val)) == expected


@pytest.mark.parametrize(
    "test_val",
    (
        "::::::::",
        "}{",
        "///}:{",
        "}:{",
        "}:",
        "/api/{version{bad}}/data",
        "/api/{version{bad}:^[a-z]{2}}/data",
        "/api/{version{bad1}:^[a-z]{2}:123}{bad2}/data",
    ),
)
def test_parse_dyn_error_input(test_val):
    with pytest.raises(AssertionError):
        list(utils.parse_dynamic(test_val))


@pytest.mark.parametrize("incomplete", ("{", "{:", "{aaa", "{:aaaa"))
def test_parse_dyn_incomplete_input(incomplete):
    assert list(utils.parse_dynamic(incomplete)) == []


@pytest.mark.parametrize(
    "bad_data",
    (
        "/api/{}/data",
        "/api/{version:^[a-z]{2}}{bad}/data",
        "/optional/{name?:[a-zA-Z]+}/{word?}",
    ),
)
def test_parse_dyn_bad(bad_data):
    with pytest.raises(ValueError):
        list(utils.parse_dynamic(bad_data))


@pytest.mark.parametrize(
    "test_val,parts",
    (
        (
            "/api/{param1}/data",
            ["/api/", utils.DynamicParseNode("{param1}", "param1"), "/data"],
        ),
        (
            "/api/{name:[0-2]+}/data",
            [
                "/api/",
                utils.DynamicParseNode("{name:[0-2]+}", "name", regex="[0-2]+"),
                "/data",
            ],
        ),
        (
            "/api/{version:^[a-z]{2}}/data",
            [
                "/api/",
                utils.DynamicParseNode(
                    "{version:^[a-z]{2}}", "version", regex="^[a-z]{2}"
                ),
                "/data",
            ],
        ),
        # ("/api/{param1}_{param2}/data", []),
        # ("/api/{param1:[a-z]{3}}_{param2}/data", []),
        # ("/api/prefix{param1:[a-z]{3}}_{param2}suffix/data", []),
    ),
)
def test_parse_dyn(test_val, parts):
    assert list(utils.parse_dynamic(test_val)) == parts
