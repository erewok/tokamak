from random import choice
from string import Formatter
from timeit import timeit

# With thanks to https://github.com/richardolsson/falcon-routing-survey for the paths below
from werkzeug.routing import Map, Rule
from werkzeug.routing.matcher import StateMachineMatcher

from tokamak.router import AsgiRouter, Route


PATHS = [
    "/",
    "/events",
    "/repos/{owner}/{repo}/events",
    "/repos/{owner}/{repo}/issues/events",
    "/networks/{owner}/{repo}/events",
    "/orgs/{org}/events",
    "/users/{username}/received_events",
    "/users/{username}/received_events/public",
    "/users/{username}/events",
    "/users/{username}/events/public",
    "/users/{username}/events/orgs/{org}",
    "/feeds",
    "/repos/{owner}/{repo}/notifications",
    "/notifications",
    "/notifications/threads/{id}",
    "/notifications/threads/{id}/subscription",
    "/repos/{owner}/{repo}/stargazers",
    "/users/{username}/starred",
    "/user/starred",
    "/user/starred/{owner}/{repo}",
    "/repos/{owner}/{repo}/subscribers",
    "/users/{username}/subscriptions",
    "/user/subscriptions",
    "/repos/{owner}/{repo}/subscription",
    "/user/subscriptions/{owner}/{repo}",
    "/repos/{owner}/{repo}/issues/events/{id}",
    "/repos/{owner}/{repo}/labels",
    "/repos/{owner}/{repo}/labels/{name}",
    "/repos/{owner}/{repo}/issues/{number}/labels",
    "/repos/{owner}/{repo}/issues/{number}/labels/{name}",
    "/repos/{owner}/{repo}/milestones/{number}/labels",
    "/repos/{owner}/{repo}/milestones",
    "/repos/{owner}/{repo}/milestones/{number}",
    "/emojis",
    "/gitignore/templates",
    "/gitignore/templates/{language}",
    "/markdown",
    "/markdown/raw",
    "/meta",
    "/rate_limit",
    "/user/orgs",
    "/users/{username}/orgs",
    "/orgs/{org}",
    "/orgs/{org}/members",
    "/orgs/{org}/members/{username}",
    "/orgs/{org}/public_members",
    "/orgs/{org}/public_members/{username}",
    "/user/memberships/orgs",
    "/user/memberships/orgs/{org}",
    "/orgs/{org}/teams",
    "/teams/{id}",
    "/teams/{id}/members",
    "/teams/{id}/members/{username}",
    "/teams/{id}/memberships/{username}",
    "/teams/{id}/repos",
    "/teams/{id}/repos/{owner}/{repo}",
    "/user/teams",
    "/orgs/{org}/hooks",
    "/orgs/{org}/hooks/{id}",
    "/orgs/{org}/hooks/{id}/pings",
    "/repos/{owner}/{repo}/pulls",
    "/repos/{owner}/{repo}/pulls/{number}",
    "/repos/{owner}/{repo}/pulls/{number}/commits",
    "/repos/{owner}/{repo}/pulls/{number}/files",
    "/repos/{owner}/{repo}/pulls/{number}/merge",
    "/repos/{owner}/{repo}/pulls/{number}/comments",
    "/repos/{owner}/{repo}/pulls/comments",
    "/repos/{owner}/{repo}/pulls/comments/{number}",
    "/users/{username}/repos",
    "/orgs/{org}/repos",
    "/repositories",
    "/user/repos",
    "/repos/{owner}/{repo}",
    "/repos/{owner}/{repo}/contributors",
    "/repos/{owner}/{repo}/languages",
    "/repos/{owner}/{repo}/teams",
    "/repos/{owner}/{repo}/tags",
    "/repos/{owner}/{repo}/branches",
    "/repos/{owner}/{repo}/branches/{branch}",
    "/repos/{owner}/{repo}/collaborators",
    "/repos/{owner}/{repo}/collaborators/{username}",
    "/repos/{owner}/{repo}/comments",
    "/repos/{owner}/{repo}/commits/{ref}/comments",
    "/repos/{owner}/{repo}/comments/{id}",
    "/repos/{owner}/{repo}/commits",
    "/repos/{owner}/{repo}/commits/{sha}",
    "/repos/{owner}/{repo}/compare/{base}...{head}",
    # "/repos/{owner}/{repo}/compare/{user1}:{branch1}...{user2}:{branch2}",
    "/repos/{owner}/{repo}/readme",
    "/repos/{owner}/{repo}/contents/{path}",
    # "/repos/{owner}/{repo}/{archive}_format/{ref}",
    "/repos/{owner}/{repo}/keys",
    "/repos/{owner}/{repo}/keys/{id}",
    "/repos/{owner}/{repo}/deployments",
    "/repos/{owner}/{repo}/deployments/{id}/statuses",
    "/repos/{owner}/{repo}/downloads",
    "/repos/{owner}/{repo}/downloads/{id}",
    "/repos/{owner}/{repo}/forks",
    "/repos/{owner}/{repo}/hooks",
    "/repos/{owner}/{repo}/hooks/{id}",
    "/repos/{owner}/{repo}/hooks/{id}/tests",
    "/repos/{owner}/{repo}/hooks/{id}/pings",
    "/repos/{owner}/{repo}/merges",
    "/repos/{owner}/{repo}/pages",
    "/repos/{owner}/{repo}/pages/builds",
    "/repos/{owner}/{repo}/pages/builds/latest",
    "/repos/{owner}/{repo}/releases",
    "/repos/{owner}/{repo}/releases/{id}",
    "/repos/{owner}/{repo}/releases/{id}/assets",
    "/repos/{owner}/{repo}/releases/assets/{id}",
    "/repos/{owner}/{repo}/stats/contributors",
    "/repos/{owner}/{repo}/stats/commit_activity",
    "/repos/{owner}/{repo}/stats/code_frequency",
    "/repos/{owner}/{repo}/stats/participation",
    "/repos/{owner}/{repo}/stats/punch_card",
    "/repos/{owner}/{repo}/statuses/{sha}",
    "/repos/{owner}/{repo}/commits/{ref}/statuses",
    "/repos/{owner}/{repo}/commits/{ref}/status",
    "/search/repositories",
    "/search/code",
    "/search/issues",
    "/search/users",
    "/users/{username}",
    "/user",
    "/users",
    "/user/emails",
    "/users/{username}/followers",
    "/user/followers",
    "/users/{username}/following",
    "/user/following",
    "/user/following/{username}",
    "/users/{username}/following/{target}_user",
    "/users/{username}/keys",
    "/user/keys",
    "/user/keys/{id}",
    "/users/{username}/site_admin",
    "/users/{username}/suspended",
    "/enterprise/stats/{type}",
    "/enterprise/settings/license",
    "/staff/indexing_jobs",
    "/setup/api/start",
    "/setup/api/upgrade",
    "/setup/api/configcheck",
    "/setup/api/configure",
    "/setup/api/settings",
    "/setup/api/maintenance",
    "/setup/api/settings/authorized-keys",
]


def handler(request):
    return None


tree_map = Map()
tree_map._matcher = StateMachineMatcher(False)
tokamak_router = AsgiRouter()


for path in PATHS:
    tree_map.add(
        Rule(path.replace("{", "<").replace("}", ">"), endpoint="a", methods=["GET"])
    )
    tokamak_router.add_route(Route(path, handler=handler, methods=["GET"]))

tree_adapter = tree_map.bind("example.org", "/")


def match(adapter, test_path):
    adapter.match(test_path)


def asgi_router_lookup(test_path):
    tokamak_router.get_route(test_path)


def main():
    print(f"{'Path'.ljust(70)} | Ratio (percent difference from baseline)")
    times = 10_000
    for _ in range(20):
        path = choice(PATHS)
        names = [fn for _, fn, _, _ in Formatter().parse(path) if fn is not None]
        test_path = path.format(**{name: "abc" for name in names})
        tree_time = timeit(
            "match(tree_adapter, test_path)",
            globals=globals() | {"test_path": test_path},
            number=times,
        )
        asgi_router_time = timeit(
            "asgi_router_lookup(test_path)",
            globals=globals() | {"test_path": test_path},
            number=times,
        )
        if asgi_router_time < tree_time:
            print(
                f"Tokamak Tree is quicker: {path.ljust(70)} | {asgi_router_time / tree_time:.2f}"
            )
        else:
            print(
                f"Werkzeug Tree is quicker: {path.ljust(70)} | {tree_time / asgi_router_time:.2f}"
            )


if __name__ == "__main__":
    main()
