from app.tools.jira_tools import get_open_tasks
from app.tools.jira_tools import get_blocked_tasks
from app.tools.jira_tools import get_overdue_tasks
from app.tools.jira_tools import get_current_sprint

def test_get_open_tasks_tool():

    result = get_open_tasks.invoke({})

    print("\nTool result:")
    print(result)

    assert result == {
        "open_tasks": 8
    }

def test_get_blocked_tasks_tool():

    result = get_blocked_tasks.invoke({})

    print("\nTool result:")
    print(result)

    assert result == {
        "blocked_tasks": 3
    }

def test_get_overdue_tasks_tool():

    result = get_overdue_tasks.invoke({})

    print("\nTool result:")
    print(result)

    assert result == {
        "overdue_tasks": 2
    }

def test_get_current_sprint_tool():

    result = get_current_sprint.invoke({})

    print("\nTool result:")
    print(result)

    assert result == {
        "current_sprint": "Sprint 14"
    }