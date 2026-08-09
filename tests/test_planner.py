from app.workflow.planner import planner


def test_planner_github_query():

    state = {
        "user_query": "Show me the latest GitHub commits"
    }

    result = planner(state)

    print("\nPlanner result:")
    print(result)

    assert result["required_sources"] == ["github"]
    assert result["status"] == "planning_completed"


def test_planner_jira_query():

    state = {
        "user_query": "Show me the overdue Jira tasks"
    }

    result = planner(state)

    print("\nPlanner result:")
    print(result)

    assert result["required_sources"] == ["jira"]
    assert result["status"] == "planning_completed"


def test_planner_broad_query():

    state = {
        "user_query": "Why is Project Alpha delayed?"
    }

    result = planner(state)

    print("\nPlanner result:")
    print(result)

    assert result["required_sources"] == ["github", "jira"]
    assert result["status"] == "planning_completed"