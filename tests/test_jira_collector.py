from app.workflow.jira_collector import jira_collector


def test_jira_collector():

    state = {
        "project": "Project Alpha"
    }

    result = jira_collector(state)

    print("\nCollector result:")
    print(result)

    assert result["status"] == "jira_collection_completed"

    assert result["jira_data"]["project"] == "Project Alpha"

    assert result["jira_data"]["open_tasks"] == 8

    assert result["jira_data"]["blocked_tasks"] == 3

    assert result["jira_data"]["overdue_tasks"] == 2

    assert result["jira_data"]["current_sprint"] == "Sprint 14"