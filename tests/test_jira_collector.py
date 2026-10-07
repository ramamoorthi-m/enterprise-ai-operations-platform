from app.workflow.jira_collector import jira_collector


class FakeTool:
    def __init__(self, result):
        self.result = result

    def invoke(self, _):
        return self.result


def test_jira_collector(monkeypatch):
    monkeypatch.setattr(
        "app.workflow.jira_collector.get_open_tasks",
        FakeTool({"project": "SCRUM", "open_tasks": 5}),
    )
    monkeypatch.setattr(
        "app.workflow.jira_collector.get_blocked_tasks",
        FakeTool({"project": "SCRUM", "blocked_tasks": 2}),
    )
    monkeypatch.setattr(
        "app.workflow.jira_collector.get_overdue_tasks",
        FakeTool({"project": "SCRUM", "overdue_tasks": 1}),
    )
    monkeypatch.setattr(
        "app.workflow.jira_collector.get_current_sprint",
        FakeTool(
            {
                "project": "SCRUM",
                "current_sprint": "Sprint 10",
                "issue_count": 3,
                "issues": [],
            }
        ),
    )

    state = {
        "project": "SCRUM",
    }

    result = jira_collector(state)

    assert result["status"] == "jira_collection_completed"

    jira_data = result["jira_data"]

    assert jira_data["project"] == "SCRUM"
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