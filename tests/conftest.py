import re
import typing

import pytest
from hypothesis import strategies

from tokamak.radix_tree import Tree

TEST_ROUTES = [
    "/",
    "/contact/",
    "/co",
    "/c",
    "/cmd/{tool}/{sub}",
    "/cmd/{tool}/",
    "/dcb/{tool}/",  # similar structure to test if ordering matters
    "/dcb/{tool}/{sub}",
    "/a/b/c/d/e/f",
    "/a/b/c/d/e/g",
    "/a/b/c/d/e/h",
    "/a/b/c/d/e/f/g/h",
    "/src/{filepath:*}",
    "/src/data",
    "/search/",
    "/search/{query}",
    "/user_{name}",
    "/user_{name}/dept",
    "/files/{dir}/{filepath:*}",
    "/doc/",
    "/doc/code_faq.html",
    "/doc/code1.html",
    "/info/{user}",
    "/info/{user}/project",
    "/info/{user}/project/{project}",
    "/info/{user}/project/{project}/dept",
    "/info/{user}/project/{project}/dept/{dept}",
    "/regex/{name:[a-zA-Z]+}/test",
    (
        "/optional/{name:[a-zA-Z]+}/{word}/plus/"
        "{uid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}}"
    ),
    "/γένωνται/{name}/aaa",
    "/darüber/schloß",
    "/darüber/schloß/ritter",
    "/hello/test",
    "/hello/{name}",
]


@pytest.fixture(scope="module")
def test_routes() -> typing.List[str]:
    return TEST_ROUTES


@pytest.fixture(scope="module")
def large_tree(test_routes: typing.List[str]) -> Tree:
    tree = Tree()
    for path in test_routes:
        tree.insert(path, path)
    return tree
