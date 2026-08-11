from app.workflow.jira_collector import jira_collector


def test_jira_collector():

    state = {
        "project": "SCRUM"
    }

    result = jira_collector(state)

    print("\nCollector result:")
    print(result)

    assert result["status"] == "jira_collection_completed"

    jira_data = result["jira_data"]

    assert jira_data["project"]
    assert isinstance(jira_data["project"], str)

    assert "open_tasks" in jira_data
    assert "blocked_tasks" in jira_data
    assert "overdue_tasks" in jira_data
    assert "current_sprint" in jira_data
    assert "issue_count" in jira_data
    assert "issues" in jira_data

    assert isinstance(jira_data["open_tasks"], int)
    assert isinstance(jira_data["blocked_tasks"], int)
    assert isinstance(jira_data["overdue_tasks"], int)
    assert isinstance(jira_data["issues"], list)