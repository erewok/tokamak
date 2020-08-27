from tokamak import radix_tree
from tokamak.radix_tree import node
from tokamak.radix_tree import tree
from tokamak.radix_tree import utils


dyn = radix_tree.DynamicNode(
    utils.DynamicParseNode(
        "{name:[a-zA-Z][0-9]{2}[a-zA-Z0-9]*}",
        "name",
        regex="[a-zA-Z][0-9]{2}[a-zA-Z0-9]*",
    )
)


def radix_tree_prefix_search():
    root = node.RadixNode("")
    root.children = [radix_tree.StaticNode("/co")]
    root.children[0].children = [
        radix_tree.StaticNode("ntact"),
        radix_tree.StaticNode("m"),
    ]
    root.children[0].children[-1].children = [
        radix_tree.StaticNode("pany"),
        radix_tree.StaticNode("e"),
    ]

    root.children[0].children[-1].children[0].children = [dyn]

    return root


TEST_ROUTES2 = [
    "/",
    "/contact/",
    "/co",
    "/c",
    "/cmd/{tool}/{sub}",
    "/cmd/{tool}/",
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
    "/info/{user}/public",
    "/info/{user}/project/{project}",
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


def mk_radix_tree():
    root = tree.Tree()
    for route in TEST_ROUTES2:
        print("INSERTING ROUTE", f"'{route}'", end="\n\n")
        root.insert(route, "a")
    return root


root = mk_radix_tree()
