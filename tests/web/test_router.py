import re

import pytest
from hypothesis import given, strategies

from tokamak.router import AsgiRouter, Route

LARGE_PATH_LIST = [
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
    # "/users/{username}/following/{target}_user",
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


@pytest.fixture(scope="module")
def large_path_to_fake_path():
    patterns = set()
    pat = re.compile(r"\{\w+\}")
    for item in LARGE_PATH_LIST:
        found_pats = pat.findall(item)
        if found_pats:
            for elem in found_pats:
                patterns.add(elem)

    def inner(original_path, replace_text):
        for item in patterns:
            if item in original_path:
                original_path = original_path.replace(item, replace_text)
        return original_path

    return inner


@given(
    route_path=strategies.sampled_from(LARGE_PATH_LIST), replace_text=strategies.text()
)
def test_router(route_path, replace_text, large_path_to_fake_path):
    router = AsgiRouter()
    router.add_route(Route(route_path, handler=lambda x: x, methods=["GET"]))
    real_path = large_path_to_fake_path(route_path, replace_text)
    assert router.get_route(real_path)
