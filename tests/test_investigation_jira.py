from types import SimpleNamespace

import pytest

from app.agents.investigation import InvestigationAgent
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
            "overdue_tasks": [
                {
                    "key": "SCRUM-101",
                    "summary": "Delayed task",
                }
            ],
        }

    async def get_current_sprint(self, project):
        return {
            "project": project,
            "sprint": "Sprint 1",
        }


class FakeGemini:

    def __init__(self):
        self.calls = 0

    def generate_with_tools(
        self,
        contents,
        tools,
        force_tool_call=False,
    ):
        self.calls += 1

        if self.calls == 1:
            return SimpleNamespace(
                function_calls=[
                    SimpleNamespace(
                        name="jira_get_overdue_tasks",
                        args={
                            "project": "SCRUM",
                        },
                    )
                ],
                candidates=[
                    SimpleNamespace(
                        content=SimpleNamespace(
                            role="model",
                            parts=[],
                        )
                    )
                ],
                text=None,
            )

        return SimpleNamespace(
            function_calls=[],
            candidates=[],
            text="Jira investigation completed.",
        )


@pytest.mark.asyncio
async def test_investigator_with_jira_mcp():

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

    llm = FakeGemini()

    investigator = InvestigationAgent(
        llm=llm,
        tools=tools,
        max_iterations=5,
    )

    plan = [
        {
            "step": 1,
            "objective": "Check the current Jira project status",
            "tools": [
                "jira_get_open_tasks",
                "jira_get_blocked_tasks",
                "jira_get_overdue_tasks",
                "jira_get_current_sprint",
            ],
        }
    ]

    state = {
        "user_query": "Why is the SCRUM project delayed?",
        "required_sources": ["jira"],
    }

    result = await investigator.investigate(
        plan=plan,
        state=state,
    )

    print("\nInvestigation result:")
    print(result)

    assert result is not None
    assert "investigation_history" in result

    assert len(result["investigation_history"]) == 1

    history_item = result["investigation_history"][0]

    assert history_item["tool"] == "jira_get_overdue_tasks"

    assert history_item["result"]["project"] == "SCRUM"
    assert "overdue_tasks" in history_item["result"]