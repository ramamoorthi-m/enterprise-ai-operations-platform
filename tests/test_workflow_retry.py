import pytest

from app.llm.client import GeminiClient
from app.llm.groq_client import GroqClient
from app.mcp.github_client import GitHubMCPClient
from app.mcp.jira_client import JiraMCPClient
from app.workflow.graph import graph


# ============================================================
# Fake Gemini response objects
# ============================================================

class FakeFunctionCall:
    def __init__(self, name, args=None):
        self.name = name
        self.args = args or {}


class FakeCandidate:
    def __init__(self):
        self.content = "Tool call requested."


class FakeToolResponse:
    def __init__(self, function_calls=None, text=""):
        self.function_calls = function_calls or []
        self.text = text
        self.candidates = [FakeCandidate()]


# ============================================================
# Track investigation attempts
# ============================================================

class FakeRetryTracker:

    planner_calls = 0
    investigation_calls = 0
    evaluator_calls = 0
    github_calls = 0
    jira_calls = 0

    @classmethod
    def reset(cls):
        cls.planner_calls = 0
        cls.investigation_calls = 0
        cls.evaluator_calls = 0
        cls.github_calls = 0
        cls.jira_calls = 0


# ============================================================
# Fake MCP connections
# ============================================================

async def fake_connect(self):
    return None


async def fake_close(self):
    return None


# ============================================================
# Fake Jira MCP methods
# ============================================================

async def fake_get_overdue_tasks(self, project):
    FakeRetryTracker.jira_calls += 1

    return {
        "project": project,
        "overdue_tasks": 1,
    }


async def fake_get_open_tasks(self, project):
    FakeRetryTracker.jira_calls += 1

    return {
        "project": project,
        "open_tasks": 5,
    }


async def fake_get_blocked_tasks(self, project):
    FakeRetryTracker.jira_calls += 1

    return {
        "project": project,
        "blocked_tasks": 0,
    }


async def fake_get_current_sprint(self, project):
    FakeRetryTracker.jira_calls += 1

    return {
        "project": project,
        "sprint": "Sprint 10",
    }


# ============================================================
# Fake GitHub MCP methods
# ============================================================

async def fake_get_recent_commits(self, repository):
    FakeRetryTracker.github_calls += 1

    return {
        "repository": repository,
        "latest_commit_sha": "abc123",
        "latest_commit_message": "Fix production issue",
    }


async def fake_get_deployment_status(self, repository):
    FakeRetryTracker.github_calls += 1

    return {
        "repository": repository,
        "deployment_status": "success",
    }


async def fake_get_repository_issues(self, repository):
    FakeRetryTracker.github_calls += 1

    return {
        "repository": repository,
        "open_issues": 0,
    }


# ============================================================
# Fake Gemini structured generation
# ============================================================

def fake_generate_structured(
    self,
    prompt,
    response_schema,
):
    schema_name = response_schema.__name__

    # --------------------------------------------------------
    # Planner
    # --------------------------------------------------------

    if schema_name == "InvestigationPlan":

        FakeRetryTracker.planner_calls += 1

        # FIRST planner attempt
        if FakeRetryTracker.planner_calls == 1:

            return response_schema.model_validate({
                "project": "SCRUM",
                "goal": (
                    "Analyze the current project status "
                    "and identify potential delivery blockers."
                ),
                "tasks": [
                    {
                        "description": (
                            "Find overdue Jira issues "
                            "and blocked tasks"
                        ),
                        "source": "jira",
                    },
                    {
                        "description": (
                            "Inspect GitHub deployment status"
                        ),
                        "source": "github",
                    },
                ],
                "required_sources": [
                    "jira",
                    "github",
                ],
            })

        # SECOND planner attempt after retry
        return response_schema.model_validate({
            "project": "SCRUM",
            "goal": (
                "Collect the missing GitHub deployment evidence."
            ),
            "tasks": [
                {
                    "description": (
                        "Inspect GitHub deployment status"
                    ),
                    "source": "github",
                },
            ],
            "required_sources": [
                "github",
            ],
        })

    # --------------------------------------------------------
    # Evaluator
    # --------------------------------------------------------

    if schema_name == "EvaluatorResult":

        FakeRetryTracker.evaluator_calls += 1

        # FIRST evaluation:
        # GitHub evidence is missing.
        if FakeRetryTracker.evaluator_calls == 1:

            return response_schema.model_validate({
                "evaluation_passed": False,
                "confidence": 0.45,
                "reason": (
                    "GitHub deployment evidence required "
                    "by the investigation plan was not collected."
                ),
                "evidence_sufficient": False,
                "retry_required": True,
                "human_review_required": False,
            })

        # SECOND evaluation:
        # GitHub evidence is now present.
        return response_schema.model_validate({
            "evaluation_passed": True,
            "confidence": 0.92,
            "reason": (
                "Required GitHub deployment evidence "
                "was collected successfully."
            ),
            "evidence_sufficient": True,
            "retry_required": False,
            "human_review_required": False,
        })

    # --------------------------------------------------------
    # Other structured agents
    # --------------------------------------------------------

    fields = response_schema.model_fields
    data = {}

    for name, field in fields.items():

        if name == "summary":
            data[name] = "Investigation evidence was collected."

        elif name == "key_findings":
            data[name] = [
                "Jira contains one overdue task.",
                "GitHub deployment status is available.",
            ]

        elif name == "risks":
            data[name] = []

        elif name == "evidence_gaps":
            data[name] = []

        elif name == "confidence":
            data[name] = 0.90

        elif name == "assessment":
            data[name] = (
                "Evidence is sufficient."
            )

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


# ============================================================
# Fake Gemini tool calling
# ============================================================

def fake_generate_with_tools(
    self,
    contents,
    tools,
    force_tool_call=False,
):
    """
    Simulate two separate InvestigationAgent executions.

    Investigation #1:
        Jira tool -> finish

    Investigation #2:
        GitHub deployment tool -> finish
    """

    FakeRetryTracker.investigation_calls += 1

    # --------------------------------------------------------
    # First investigation
    # --------------------------------------------------------

    if FakeRetryTracker.investigation_calls == 1:

        return FakeToolResponse(
            function_calls=[
                FakeFunctionCall(
                    name="jira_get_overdue_tasks",
                    args={
                        "project": "SCRUM",
                    },
                )
            ]
        )

    # --------------------------------------------------------
    # Second call belongs to the SAME investigation.
    # Finish first investigation.
    # --------------------------------------------------------

    if FakeRetryTracker.investigation_calls == 2:

        return FakeToolResponse(
            function_calls=[],
            text=(
                "Jira investigation completed, "
                "but GitHub evidence was not collected."
            ),
        )

    # --------------------------------------------------------
    # Third call = second investigation attempt
    # --------------------------------------------------------

    if FakeRetryTracker.investigation_calls == 3:

        return FakeToolResponse(
            function_calls=[
                FakeFunctionCall(
                    name="github_get_deployment_status",
                    args={
                        "repository": (
                            "ramamoorthi-m/"
                            "enterprise-ai-operations-platform"
                        ),
                    },
                )
            ]
        )

    # --------------------------------------------------------
    # Fourth call = finish second investigation
   # --------------------------------------------------------

    return FakeToolResponse(
        function_calls=[],
        text=(
            "GitHub deployment evidence collected. "
            "Investigation completed."
        ),
    )


# ============================================================
# Fake normal Gemini generation
# ============================================================

def fake_generate(self, prompt):

    return (
        "# Enterprise Project Investigation Report\n\n"
        "## Executive Summary\n"
        "Investigation completed successfully.\n\n"
        "## Key Findings\n"
        "- Jira contains one overdue task.\n"
        "- GitHub deployment status is available.\n\n"
        "## Risks\n"
        "- One overdue Jira task requires attention.\n"
    )


# ============================================================
# Test
# ============================================================

@pytest.mark.asyncio
async def test_retry_recovers_missing_evidence(monkeypatch):

    FakeRetryTracker.reset()

    # --------------------------------------------------------
    # Mock Gemini
    # --------------------------------------------------------

    monkeypatch.setattr(
        GeminiClient,
        "generate_structured",
        fake_generate_structured,
    )

    monkeypatch.setattr(
        GeminiClient,
        "generate",
        fake_generate,
    )

    monkeypatch.setattr(
        GeminiClient,
        "generate_with_tools",
        fake_generate_with_tools,
    )

    monkeypatch.setattr(
        GroqClient,
        "generate_structured",
        fake_generate_structured,
    )

    # --------------------------------------------------------
    # Mock MCP connections
    # --------------------------------------------------------

    monkeypatch.setattr(
        JiraMCPClient,
        "connect",
        fake_connect,
    )

    monkeypatch.setattr(
        JiraMCPClient,
        "close",
        fake_close,
    )

    monkeypatch.setattr(
        GitHubMCPClient,
        "connect",
        fake_connect,
    )

    monkeypatch.setattr(
        GitHubMCPClient,
        "close",
        fake_close,
    )

    # --------------------------------------------------------
    # Mock Jira MCP operations
    # --------------------------------------------------------

    monkeypatch.setattr(
        JiraMCPClient,
        "get_overdue_tasks",
        fake_get_overdue_tasks,
    )

    monkeypatch.setattr(
        JiraMCPClient,
        "get_open_tasks",
        fake_get_open_tasks,
    )

    monkeypatch.setattr(
        JiraMCPClient,
        "get_blocked_tasks",
        fake_get_blocked_tasks,
    )

    monkeypatch.setattr(
        JiraMCPClient,
        "get_current_sprint",
        fake_get_current_sprint,
    )

    # --------------------------------------------------------
    # Mock GitHub MCP operations
    # --------------------------------------------------------

    monkeypatch.setattr(
        GitHubMCPClient,
        "get_recent_commits",
        fake_get_recent_commits,
    )

    monkeypatch.setattr(
        GitHubMCPClient,
        "get_deployment_status",
        fake_get_deployment_status,
    )

    monkeypatch.setattr(GitHubMCPClient,
        "get_repository_issues",
        fake_get_repository_issues,
    )

    # --------------------------------------------------------
    # Initial state
    # --------------------------------------------------------

    initial_state = {
        "user_query": (
            "Analyze the current project status "
            "and identify potential delivery blockers."
        ),

        "project": "SCRUM",

        "plan": [],
        "required_sources": [],

        "github_data": {},
        "jira_data": {},
        "doc_data": {},
        "slack_data": {},

        "findings": [],
        "report": "",

        "analysis": {},

        "confidence": 0.0,
        "human_review_required": False,

        "errors": [],
        "status": "",

        "evaluation_passed": False,
        "evidence_sufficient": False,
        "retry_required": False,

        "retry_count": 0,
        "max_retries": 2,
    }

    # --------------------------------------------------------
    # Run workflow
    # --------------------------------------------------------

    result = await graph.ainvoke(
        initial_state,
        config={
            "configurable": {
                "thread_id": "test-retry-recovery",
            }
        },
    )

    print("\nRETRY WORKFLOW FINAL STATE:")
    print(result)

    # --------------------------------------------------------
    # Core workflow assertions
    # --------------------------------------------------------

    assert result["status"] == "report_generated"

    assert result["evaluation_passed"] is True

    assert result["confidence"] > 0

    assert result["report"]

    # --------------------------------------------------------
    # Retry actually happened
    # --------------------------------------------------------

    assert result["retry_count"] == 1

    assert FakeRetryTracker.planner_calls == 2

    assert FakeRetryTracker.evaluator_calls == 2

    # --------------------------------------------------------
    # Jira was investigated
    # --------------------------------------------------------

    assert FakeRetryTracker.jira_calls >= 1

    # --------------------------------------------------------
    # GitHub was investigated during retry
    # --------------------------------------------------------

    assert FakeRetryTracker.github_calls >= 1

    assert (
        "github_get_deployment_status"
        in result["github_data"]
    )

    # --------------------------------------------------------
    # Final evidence should contain GitHub deployment data
    # --------------------------------------------------------

    assert (
        result["github_data"]
        ["github_get_deployment_status"]
        ["deployment_status"]
        == "success"
    )

    # --------------------------------------------------------
    # Final workflow succeeded after retry
    # --------------------------------------------------------

    assert result["investigation_complete"] is True