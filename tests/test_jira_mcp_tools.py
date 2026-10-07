import pytest
from app.tools.jira_mcp_tools import JiraMCPToolProvider


class FakeJiraClient:

    async def get_open_tasks(self, project):
        return {
            "project": project,
            "open_tasks": [],
        }

    async def get_blocked_tasks(self, project):
        return {
            "project": project,
            "blocked_tasks": [],
        }

    async def get_overdue_tasks(self, project):
        return {
            "project": project,
            "overdue_tasks": [],
        }

    async def get_current_sprint(self, project):
        return {
            "project": project,
            "sprint": "Sprint 1",
        }


@pytest.mark.anyio
async def test_jira_mcp_tools():

    client = FakeJiraClient()

    provider = JiraMCPToolProvider(client)

    tools = provider.get_tools()

    assert len(tools) == 4

    tool_names = {
        tool.name
        for tool in tools
    }

    assert "jira_get_open_tasks" in tool_names
    assert "jira_get_blocked_tasks" in tool_names
    assert "jira_get_overdue_tasks" in tool_names
    assert "jira_get_current_sprint" in tool_names

    result = await provider.jira_get_open_tasks("SCRUM")

    assert result["project"] == "SCRUM"
    assert "open_tasks" in result