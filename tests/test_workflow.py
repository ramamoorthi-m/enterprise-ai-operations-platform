import pytest
from app.workflow.graph import graph
from app.llm.client import GeminiClient



def fake_generate(self, prompt: str) -> str:
    return """
    The investigation identified outstanding Jira work and recent
    GitHub development activity.

    GitHub:
    Recent development activity was detected in the repository.

    Jira:
    Outstanding work was detected in the SCRUM project.

    Root Cause:
    Outstanding Jira work requires attention.

    Recommended Actions:
    Review and prioritize the outstanding Jira work.
    """


def fake_generate_structured(self, prompt: str, response_schema):
    fields = response_schema.model_fields
    data = {}

    for name, field in fields.items():

        if name == "goal":
            data[name] = (
                "Analyze the current project status and identify "
                "potential delivery blockers."
            )

        elif name == "project":
            data[name] = "SCRUM"

        elif name == "required_sources":
            data[name] = ["jira", "github"]

        elif name == "tasks":
            data[name] = [
                {
                    "description": "Find overdue Jira issues and blocked tasks",
                    "source": "jira",
                },
                {
                    "description": "Inspect recent GitHub commits and deployment status",
                    "source": "github",
                },
            ]

        elif name in ("passed", "evaluation_passed"):
            data[name] = True

        elif name == "confidence":
            data[name] = 0.90

        elif name == "human_review_required":
            data[name] = False

        elif name in ("findings", "sources"):
            data[name] = [
                "Jira contains outstanding work.",
                "GitHub contains recent development activity.",
            ]

        elif field.annotation is str:
            data[name] = "Investigation completed."

        elif field.annotation is bool:
            data[name] = False

        elif field.annotation is float:
            data[name] = 0.90

        elif field.annotation is int:
            data[name] = 0

        elif "list" in str(field.annotation).lower():
            data[name] = []

        elif "dict" in str(field.annotation).lower():
            data[name] = {}

    return response_schema.model_validate(data)


# ------------------------------------------------------------------
# Fake Gemini tool-calling response objects
# ------------------------------------------------------------------


class FakeFunctionCall:
    def __init__(self, name, args=None):
        self.name = name
        self.args = args or {}


class FakeCandidate:
    def __init__(self):
        self.content = "Investigation completed."


class FakeToolResponse:
    def __init__(self, function_calls=None, text=""):
        self.function_calls = function_calls or []
        self.text = text
        self.candidates = [FakeCandidate()]


# ------------------------------------------------------------------
# Fake Gemini tool calling
# ------------------------------------------------------------------

_tool_call_count = 0


def fake_generate_with_tools(self, contents, tools, force_tool_call=False,):
    """
    Fake Gemini tool-calling response.

    First call:
        Request Jira and GitHub tools.

    Second call:
        Finish the investigation.

    No real Gemini API call is made.
    """

    global _tool_call_count

    _tool_call_count += 1

    if _tool_call_count == 1:
        return FakeToolResponse(
            function_calls=[
                FakeFunctionCall(
                    name="jira_get_overdue_tasks",
                    args={"project": "SCRUM"},
                ),
                FakeFunctionCall(
                    name="github_get_recent_commits",
                    args={
                        "repository": "ramamoorthi-m/enterprise-ai-operations-platform"
                    },
                ),
            ],
            text=(
                "I need Jira and GitHub evidence "
                "before completing the investigation."
            ),
        )

    return FakeToolResponse(
        function_calls=[],
        text=(
            "Investigation completed. "
            "Jira shows outstanding work. "
            "GitHub shows recent development activity."
        ),
    )


# ------------------------------------------------------------------
# Enterprise workflow test
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enterprise_workflow(monkeypatch):

    global _tool_call_count
    _tool_call_count = 0

    # Mock normal Gemini generation.
    monkeypatch.setattr(
        GeminiClient,
        "generate",
        fake_generate,
    )

    # Mock structured Gemini generation.
    monkeypatch.setattr(
        GeminiClient,
        "generate_structured",
        fake_generate_structured,
    )

    # Mock Gemini tool calling.
    monkeypatch.setattr(
        GeminiClient,
        "generate_with_tools",
        fake_generate_with_tools,
    )

    initial_state = {
        "user_query": "Analyze the current project status and identify potential delivery blockers.",

        "project": "SCRUM",

        "plan": [],

        "required_sources": [],

        "github_data": {},
        "jira_data": {},
        "doc_data": {},
        "slack_data": {},

        "findings": [],

        "report": "",

        "confidence": 0.0,

        "human_review_required": False,

        "errors": [],

        "status": "",

        "evaluation_passed": False,

        "retry_count": 0,
        "max_retries": 2,
    }

    result = await graph.ainvoke(
        initial_state,
        config={
            "configurable": {
                "thread_id": "test-enterprise-workflow",
            }
        },
    )

    print("\nFINAL STATE:")
    print(result)

    assert result["status"] == "report_generated"
    assert result["report"]
    assert result["findings"]

    assert result["evaluation_passed"] is True
    assert result["confidence"] > 0
    assert result["required_sources"]

    assert "GitHub" in result["report"]
    assert "Jira" in result["report"]