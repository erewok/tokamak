
import pytest
from tokamak.radix_tree import tree


@pytest.mark.parametrize("default_handler", (None, "A"))
@pytest.mark.parametrize(
    "tsm", (tree.TrailingSlashMatch.RELAXED, tree.TrailingSlashMatch.STRICT)
)
def test_tree_ctor(
    default_handler: str | None, tsm: tree.TrailingSlashMatch
) -> None:
    new_tree = tree.Tree(default_handler=default_handler, trailing_slash_match=tsm)
    if default_handler:
        assert new_tree._root.leaf is not None
        assert new_tree._root.leaf.handler == default_handler
    else:
        assert new_tree._root.leaf is None


@pytest.mark.parametrize("default_handler", (None, "A"))
@pytest.mark.parametrize(
    "tsm", (tree.TrailingSlashMatch.RELAXED, tree.TrailingSlashMatch.STRICT)
)
def test_insert(default_handler: str | None, tsm: tree.TrailingSlashMatch) -> None:
    new_tree = tree.Tree(default_handler=default_handler, trailing_slash_match=tsm)
    with pytest.raises(ValueError):
        new_tree.insert("bla", "A")

    new_tree.insert("/bla/", "A")
    if tsm is tree.TrailingSlashMatch.RELAXED:
        assert next(iter(new_tree._root.children)).path == "/bla"
    else:
        assert next(iter(new_tree._root.children)).path == "/bla/"


@pytest.mark.parametrize("default_handler", (None, "A"))
@pytest.mark.parametrize(
    "tsm", (tree.TrailingSlashMatch.RELAXED, tree.TrailingSlashMatch.STRICT)
)
def test_get_handler(
    default_handler: str | None, tsm: tree.TrailingSlashMatch
) -> None:
    new_tree = tree.Tree(default_handler=default_handler, trailing_slash_match=tsm)
    new_tree.insert("/bla/{ingredient}", "B")
    new_tree.insert("/claw/", "B")

    result, ctx = new_tree.get_handler("/")
    assert ctx == {}
    if default_handler:
        assert result == "A"
    else:
        assert result is None

    result, ctx = new_tree.get_handler("/bla")
    assert ctx == {}
    if default_handler:
        assert result == "A"
    else:
        assert result is None

    result, ctx = new_tree.get_handler("/bla/sugar")
    assert ctx == {"ingredient": "sugar"}
    assert result == "B"

    result, ctx = new_tree.get_handler("/bla/sugar/")
    assert ctx == {"ingredient": "sugar"}
    if tsm is tree.TrailingSlashMatch.RELAXED:
        assert result == "B"
    elif default_handler:
        assert result == "A"
    else:
        assert result is None

    result, ctx = new_tree.get_handler("/claw")
    assert ctx == {}
    if tsm is tree.TrailingSlashMatch.RELAXED:
        assert result == "B"
    elif default_handler:
        assert result == "A"
    else:
        assert result is None

    result, ctx = new_tree.get_handler("/claw/")
    assert ctx == {}
    assert result == "B"
