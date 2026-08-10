from app.workflow.planner import planner


def test_planner_node():
    state = {
        "user_query": "Analyze the current project status and identify potential delivery blockers."
    }

    result = planner(state)

    print("\nPlanner node result:")
    print(result)

    assert result["status"] == "planning_completed"
    assert len(result["plan"]) > 0
    assert len(result["required_sources"]) > 0

    for source in result["required_sources"]:
        assert source in {"github", "jira"}