from app.tools.jira_tools import (
    get_open_tasks,
    get_blocked_tasks,
    get_overdue_tasks,
    get_current_sprint,
)


def test_get_open_tasks_tool():

    result = get_open_tasks.invoke({})

    print("\nTool result:")
    print(result)

    assert "project" in result
    assert "open_tasks" in result

    assert isinstance(result["project"], str)
    assert isinstance(result["open_tasks"], int)
    assert result["open_tasks"] >= 0


def test_get_blocked_tasks_tool():

    result = get_blocked_tasks.invoke({})

    print("\nTool result:")
    print(result)

    assert "project" in result
    assert "blocked_tasks" in result

    assert isinstance(result["project"], str)
    assert isinstance(result["blocked_tasks"], int)
    assert result["blocked_tasks"] >= 0


def test_get_overdue_tasks_tool():

    result = get_overdue_tasks.invoke({})

    print("\nTool result:")
    print(result)

    assert "project" in result
    assert "overdue_tasks" in result

    assert isinstance(result["project"], str)
    assert isinstance(result["overdue_tasks"], int)
    assert result["overdue_tasks"] >= 0


def test_get_current_sprint_tool():

    result = get_current_sprint.invoke({})

    print("\nTool result:")
    print(result)

    assert "project" in result
    assert "current_sprint" in result
    assert "issue_count" in result
    assert "issues" in result

    assert isinstance(result["project"], str)
    assert isinstance(result["current_sprint"], str)
    assert isinstance(result["issue_count"], int)
    assert isinstance(result["issues"], list)