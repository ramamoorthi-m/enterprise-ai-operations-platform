from app.workflow.router import (
    route_after_planner,
    route_after_github,
)


def test_route_github_first():

    state = {
        "required_sources": ["github", "jira"]
    }

    result = route_after_planner(state)

    assert result == "github"


def test_route_jira_first():

    state = {
        "required_sources": ["jira"]
    }

    result = route_after_planner(state)

    assert result == "jira"


def test_route_after_github_to_jira():

    state = {
        "required_sources": ["github", "jira"]
    }

    result = route_after_github(state)

    assert result == "jira"


def test_route_after_github_to_aggregator():

    state = {
        "required_sources": ["github"]
    }

    result = route_after_github(state)

    assert result == "aggregator"