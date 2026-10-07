import pytest
from app.agents.investigation import InvestigationAgent


class FakeFunctionCall:
    def __init__(self, name, args=None):
        self.name = name
        self.args = args or {}


class FakeCandidate:
    def __init__(self):
        self.content = "Tool failure received."


class FakeResponse:
    def __init__(self, function_calls=None, text=""):
        self.function_calls = function_calls or []
        self.text = text
        self.candidates = [FakeCandidate()]


class FailingLLM:

    def __init__(self):
        self.calls = 0

    def generate_with_tools(self, contents, tools, force_tool_call=False):

        self.calls += 1

        if self.calls == 1:
            return FakeResponse(
                function_calls=[
                    FakeFunctionCall(
                        name="failing_tool",
                        args={"project": "SCRUM"},
                    )
                ]
            )

        return FakeResponse(
            function_calls=[],
            text="Investigation completed despite tool failure.",
        )


def failing_tool(project: str):
    raise RuntimeError("Jira API unavailable")


failing_tool.name = "failing_tool"

@pytest.mark.asyncio
async def test_investigation_handles_tool_error():

    llm = FailingLLM()

    agent = InvestigationAgent(
        llm=llm,
        tools=[failing_tool],
        max_iterations=3,
    )

    result = await agent.investigate(
        plan=[
            {
                "description": "Check Jira tasks",
                "source": "jira",
            }
        ],
        state={
            "user_query": "Why is the project delayed?",
        },
    )

    assert result["investigation_complete"] is True

    assert len(result["investigation_history"]) == 1

    history_item = result["investigation_history"][0]

    assert history_item["tool"] == "failing_tool"

    assert history_item["result"]["tool"] == "failing_tool"

    assert "Jira API unavailable" in history_item["result"]["error"]

    assert (
    history_item["result"]["failure_category"]
    == "tool_execution_failure"
    )

    assert "failures" in result


class InvalidToolLLM:

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
            return FakeResponse(
                function_calls=[
                    FakeFunctionCall(
                        name="nonexistent_tool",
                        args={"project": "SCRUM"},
                    )
                ]
            )

        return FakeResponse(
            function_calls=[],
            text="Investigation completed.",
        )


@pytest.mark.asyncio
async def test_investigation_handles_invalid_tool_call():

    llm = InvalidToolLLM()

    agent = InvestigationAgent(
        llm=llm,
        tools=[failing_tool],
        max_iterations=3,
    )

    result = await agent.investigate(
        plan=[
            {
                "description": "Check Jira tasks",
                "source": "jira",
            }
        ],
        state={
            "user_query": "Why is the project delayed?",
        },
    )

    assert result["investigation_complete"] is True

    assert len(result["investigation_history"]) == 1

    history_item = result["investigation_history"][0]

    assert history_item["tool"] == "nonexistent_tool"

    assert (
        history_item["result"]["failure_category"]
        == "invalid_tool_call"
    )

    assert len(result["failures"]) == 1

    failure = result["failures"][0]

    assert failure["category"] == "invalid_tool_call"
    assert failure["source"] == "investigation_agent"
    assert failure["retryable"] is False
    assert failure["blocking"] is False