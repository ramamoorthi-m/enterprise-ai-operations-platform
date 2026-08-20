import pytest
from types import SimpleNamespace

from app.agents.investigation import InvestigationAgent
from app.mcp.jira_client import JiraMCPClient
from app.tools.jira_mcp_tools import JiraMCPToolProvider

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

    client = JiraMCPClient()

    await client.connect()

    try:
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
        }

        result = await investigator.investigate(
            plan=plan,
            state=state,
        )

        print("\nInvestigation result:")
        print(result)

        assert result is not None
        assert "investigation_history" in result

    finally:
        await client.close()