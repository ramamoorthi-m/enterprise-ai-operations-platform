import requests

from app.tools.jira_tools import (
    get_open_tasks,
    get_blocked_tasks,
    get_overdue_tasks,
    get_current_sprint,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.status_code = 200
        self.url = "https://fake-jira.example/rest/api/3/search/jql"
        self.text = "{}"

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def test_get_open_tasks_tool(monkeypatch):
    monkeypatch.setattr(
        requests,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "issues": [
                    {"key": "SCRUM-1"},
                    {"key": "SCRUM-2"},
                    {"key": "SCRUM-3"},
                ]
            }
        ),
    )

    result = get_open_tasks.invoke({})

    assert "project" in result
    assert "open_tasks" in result

    assert isinstance(result["project"], str)
    assert isinstance(result["open_tasks"], int)
    assert result["open_tasks"] == 3


def test_get_blocked_tasks_tool(monkeypatch):
    monkeypatch.setattr(
        requests,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "issues": [
                    {"key": "SCRUM-4"},
                    {"key": "SCRUM-5"},
                ]
            }
        ),
    )

    result = get_blocked_tasks.invoke({})

    assert "project" in result
    assert "blocked_tasks" in result

    assert isinstance(result["project"], str)
    assert isinstance(result["blocked_tasks"], int)
    assert result["blocked_tasks"] == 2


def test_get_overdue_tasks_tool(monkeypatch):
    monkeypatch.setattr(
        requests,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "issues": [
                    {"key": "SCRUM-6"},
                ]
            }
        ),
    )

    result = get_overdue_tasks.invoke({})

    assert "project" in result
    assert "overdue_tasks" in result

    assert isinstance(result["project"], str)
    assert isinstance(result["overdue_tasks"], int)
    assert result["overdue_tasks"] == 1


def test_get_current_sprint_tool(monkeypatch):
    monkeypatch.setattr(
        requests,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "issues": [
                    {
                        "key": "SCRUM-7",
                        "fields": {
                            "summary": "Implement authentication"
                        },
                    },
                    {
                        "key": "SCRUM-8",
                        "fields": {
                            "summary": "Fix deployment pipeline"
                        },
                    },
                ]
            }
        ),
    )

    result = get_current_sprint.invoke({})

    assert "project" in result
    assert "current_sprint" in result
    assert "issue_count" in result
    assert "issues" in result

    assert isinstance(result["project"], str)
    assert isinstance(result["current_sprint"], str)
    assert isinstance(result["issue_count"], int)
    assert isinstance(result["issues"], list)

    assert result["current_sprint"] == "active"
    assert result["issue_count"] == 2
    assert result["issues"] == [
        {
            "key": "SCRUM-7",
            "summary": "Implement authentication",
        },
        {
            "key": "SCRUM-8",
            "summary": "Fix deployment pipeline",
        },
    ]