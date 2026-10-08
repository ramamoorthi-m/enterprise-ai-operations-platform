from app.workflow.router import (
    route_after_planner,
    route_after_github,
    route_after_evaluation,
    route_after_human_review,
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


def test_route_after_evaluation_to_human_review():

    state = {
        "human_review_required": True,
        "evaluation_passed": False,
        "retry_required": False,
    }

    result = route_after_evaluation(state)

    assert result == "human_review"


def test_route_after_evaluation_to_success():

    state = {
        "human_review_required": False,
        "evaluation_passed": True,
        "retry_required": False,
    }

    result = route_after_evaluation(state)

    assert result == "success"


def test_route_after_evaluation_to_retry():

    state = {
        "human_review_required": False,
        "evaluation_passed": False,
        "retry_required": True,
        "retry_count": 0,
        "max_retries": 2,
    }

    result = route_after_evaluation(state)

    assert result == "retry"


def test_route_after_evaluation_retry_limit_reached():

    state = {
        "human_review_required": False,
        "evaluation_passed": False,
        "retry_required": True,
        "retry_count": 2,
        "max_retries": 2,
    }

    result = route_after_evaluation(state)

    assert result == "failed"


def test_route_after_evaluation_to_failed():

    state = {
        "human_review_required": False,
        "evaluation_passed": False,
        "retry_required": False,
    }

    result = route_after_evaluation(state)

    assert result == "failed"


def test_route_after_evaluation_human_review_has_precedence():

    state = {
        "human_review_required": True,
        "evaluation_passed": True,
        "retry_required": True,
        "retry_count": 0,
        "max_retries": 2,
    }

    result = route_after_evaluation(state)

    assert result == "human_review"


def test_route_after_human_review_approve():

    state = {
        "human_review_decision": "approve",
    }

    result = route_after_human_review(state)

    assert result == "success"


def test_route_after_human_review_retry():

    state = {
        "human_review_decision": "retry",
        "retry_count": 0,
        "max_retries": 2,
    }

    result = route_after_human_review(state)

    assert result == "retry"


def test_route_after_human_review_retry_limit_reached():

    state = {
        "human_review_decision": "retry",
        "retry_count": 2,
        "max_retries": 2,
    }

    result = route_after_human_review(state)

    assert result == "failed"


def test_route_after_human_review_reject():

    state = {
        "human_review_decision": "reject",
    }

    result = route_after_human_review(state)

    assert result == "failed"