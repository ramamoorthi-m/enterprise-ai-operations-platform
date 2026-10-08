import pytest

from app.workflow.graph import graph
from app.workflow.investigator import investigator
from app.llm.client import GeminiClient
from app.llm.groq_client import GroqClient
from langgraph.types import Command


# ------------------------------------------------------------------
# Fake MCP clients
# ------------------------------------------------------------------


class FakeGitHubClient:

    async def connect(self):
        pass

    async def close(self):
        pass

    async def get_repository_issues(self, repository):
        return {
            "repository": repository,
            "open_issues": 0,
        }

    async def get_recent_commits(self, repository):
        return {
            "repository": repository,
            "latest_commit_sha": "test-sha",
            "latest_commit_message": "Test commit",
            "latest_commit_author": "test-author",
            "latest_commit_date": "2026-08-11T00:00:00Z",
        }

    async def get_deployment_status(self, repository):
        return {
            "repository": repository,
            "deployment_status": "success",
        }


class FakeJiraClient:

    async def connect(self):
        pass

    async def close(self):
        pass

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


# ------------------------------------------------------------------
# Failing MCP clients
# ------------------------------------------------------------------


class FailingJiraClient:

    async def connect(self):
        raise RuntimeError("Jira MCP unavailable")

    async def close(self):
        pass


class FailingGitHubClient:

    async def connect(self):
        raise RuntimeError("GitHub MCP unavailable")

    async def close(self):
        pass


# ------------------------------------------------------------------
# Fake Gemini generation
# ------------------------------------------------------------------


def fake_generate(self, prompt: str) -> str:
    return """
    # Enterprise Project Investigation Report

    ## Investigation Request
    Analyze the current project status and identify potential delivery blockers.

    ## Executive Summary
    The investigation identified outstanding Jira work and recent
    GitHub development activity.

    ## Key Findings
    GitHub:
    Recent development activity was detected in the repository.

    Jira:
    Outstanding work was detected in the SCRUM project.

    ## Risks
    Outstanding Jira work requires attention.

    ## Evidence Gaps
    No major evidence gaps identified.

    ## Confidence
    High confidence based on the collected evidence.
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

        elif name == "evidence_sufficient":
            data[name] = True

        elif name == "retry_required":
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


def fake_generate_with_tools(
    self,
    contents,
    tools,
    force_tool_call=False,
):
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
                        "repository": (
                            "ramamoorthi-m/"
                            "enterprise-ai-operations-platform"
                        )
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

    # --------------------------------------------------------------
    # Mock MCP clients
    # --------------------------------------------------------------

    monkeypatch.setattr(
        "app.workflow.investigator.GitHubMCPClient",
        FakeGitHubClient,
    )

    monkeypatch.setattr(
        "app.workflow.investigator.JiraMCPClient",
        FakeJiraClient,
    )

    # --------------------------------------------------------------
    # Mock normal Gemini generation
    # --------------------------------------------------------------

    monkeypatch.setattr(
        GeminiClient,
        "generate",
        fake_generate,
    )

    # --------------------------------------------------------------
    # Mock structured Gemini generation
    # --------------------------------------------------------------

    monkeypatch.setattr(
        GeminiClient,
        "generate_structured",
        fake_generate_structured,
    )

    # --------------------------------------------------------------
    # Mock structured Groq generation
    # --------------------------------------------------------------

    monkeypatch.setattr(
        GroqClient,
        "generate_structured",
        fake_generate_structured,
    )

    monkeypatch.setattr(
        GroqClient,
        "generate",
        fake_generate,
    )

    # --------------------------------------------------------------
    # Mock Gemini tool calling
    # --------------------------------------------------------------

    monkeypatch.setattr(
        GeminiClient,
        "generate_with_tools",
        fake_generate_with_tools,
    )

    # --------------------------------------------------------------
    # Initial workflow state
    # --------------------------------------------------------------

    initial_state = {
        "user_query": (
            "Analyze the current project status and "
            "identify potential delivery blockers."
        ),

        "project": "SCRUM",

        "plan": [],

        "required_sources": [],

        "github_data": {},
        "jira_data": {},
        "doc_data": {},
        "slack_data": {},

        "findings": [],

        "evidence": [],

        "investigation_history": [],
        "investigation_iteration": 0,
        "max_investigation_iterations": 5,
        "investigation_complete": False,

        "report": "",

        "confidence": 0.0,

        "human_review_required": False,
        "human_review_decision": "",
        "human_review_reason": "",

        "errors": [],
        "failures": [],

        "status": "",

        "evaluation_passed": False,

        "retry_count": 0,
        "max_retries": 2,
        "retry_required": False,
    }

    # --------------------------------------------------------------
    # Run complete LangGraph workflow
    # --------------------------------------------------------------

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

    # --------------------------------------------------------------
    # Workflow assertions
    # --------------------------------------------------------------

    assert result["status"] == "report_generated"

    assert result["report"]

    assert result["findings"]

    assert result["evaluation_passed"] is True

    assert result["confidence"] > 0

    assert result["required_sources"]

    # --------------------------------------------------------------
    # Evidence contract assertions
    # --------------------------------------------------------------

    assert result["evidence"]

    successful_evidence = [
        item
        for item in result["evidence"]
        if item["status"] == "success"
    ]

    assert len(successful_evidence) == 4

    evidence_tools = {
        item["tool"]
        for item in successful_evidence
    }

    assert "jira_get_overdue_tasks" in evidence_tools
    assert "github_get_recent_commits" in evidence_tools

    # --------------------------------------------------------------
    # Report assertions
    # --------------------------------------------------------------

    report = result["report"]

    assert report

    required_sections = [
        "## Investigation Request",
        "## Executive Summary",
        "## Key Findings",
        "## Risks",
        "## Evidence Gaps",
        "## Confidence",
    ]

    for section in required_sections:
        assert section in report


# ------------------------------------------------------------------
# Jira connection failure
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_jira_connection_failure_is_structured(monkeypatch):

    monkeypatch.setattr(
        "app.workflow.investigator.JiraMCPClient",
        FailingJiraClient,
    )

    monkeypatch.setattr(
        "app.workflow.investigator.GitHubMCPClient",
        FakeGitHubClient,
    )

    monkeypatch.setattr(
        GeminiClient,
        "generate_with_tools",
        fake_generate_with_tools,
    )

    result = await investigator(
        {
            "required_sources": ["jira", "github"],
            "project": "SCRUM",
            "plan": [
                {
                    "description": "Check Jira overdue tasks",
                    "source": "jira",
                },
                {
                    "description": "Inspect GitHub commits",
                    "source": "github",
                },
            ],
            "user_query": "Why is the project delayed?",
            "github_repository": (
                "ramamoorthi-m/"
                "enterprise-ai-operations-platform"
            ),
        }
    )

    assert "failures" in result

    jira_failures = [
        failure
        for failure in result["failures"]
        if failure["source"] == "jira"
    ]

    assert len(jira_failures) == 1

    failure = jira_failures[0]

    assert failure["category"] == "connection_failure"
    assert failure["source"] == "jira"
    assert failure["retryable"] is True
    assert failure["blocking"] is True
    assert "Jira MCP unavailable" in failure["message"]


# ------------------------------------------------------------------
# GitHub connection failure
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_github_connection_failure_is_structured(monkeypatch):

    monkeypatch.setattr(
        "app.workflow.investigator.GitHubMCPClient",
        FailingGitHubClient,
    )

    monkeypatch.setattr(
        "app.workflow.investigator.JiraMCPClient",
        FakeJiraClient,
    )

    monkeypatch.setattr(
        GeminiClient,
        "generate_with_tools",
        fake_generate_with_tools,
    )

    result = await investigator(
        {
            "required_sources": ["jira", "github"],
            "project": "SCRUM",
            "plan": [
                {
                    "description": "Check Jira overdue tasks",
                    "source": "jira",
                },
                {
                    "description": "Inspect GitHub commits",
                    "source": "github",
                },
            ],
            "user_query": "Why is the project delayed?",
            "github_repository": (
                "ramamoorthi-m/"
                "enterprise-ai-operations-platform"
            ),
        }
    )

    assert "failures" in result

    github_failures = [
        failure
        for failure in result["failures"]
        if failure["source"] == "github"
    ]

    assert len(github_failures) == 1

    failure = github_failures[0]

    assert failure["category"] == "connection_failure"
    assert failure["source"] == "github"
    assert failure["retryable"] is True
    assert failure["blocking"] is True
    assert "GitHub MCP unavailable" in failure["message"]


# ------------------------------------------------------------------
# Partial dependency failure
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_one_mcp_failure_does_not_block_other_source(
    monkeypatch,
):

    monkeypatch.setattr(
        "app.workflow.investigator.JiraMCPClient",
        FailingJiraClient,
    )

    monkeypatch.setattr(
        "app.workflow.investigator.GitHubMCPClient",
        FakeGitHubClient,
    )

    monkeypatch.setattr(
        GeminiClient,
        "generate_with_tools",
        fake_generate_with_tools,
    )

    result = await investigator(
        {
            "required_sources": ["jira", "github"],
            "project": "SCRUM",
            "plan": [
                {
                    "description": "Check Jira overdue tasks",
                    "source": "jira",
                },
                {
                    "description": "Inspect GitHub commits",
                    "source": "github",
                },
            ],
            "user_query": "Why is the project delayed?",
            "github_repository": (
                "ramamoorthi-m/"
                "enterprise-ai-operations-platform"
            ),
        }
    )

    # --------------------------------------------------------------
    # Jira connection failure must be recorded.
    # --------------------------------------------------------------

    jira_failures = [
        failure
        for failure in result["failures"]
        if failure["source"] == "jira"
    ]

    assert len(jira_failures) == 1

    assert (
        jira_failures[0]["category"]
        == "connection_failure"
    )

    # --------------------------------------------------------------
    # GitHub investigation must still execute.
    # --------------------------------------------------------------

    github_history = [
        item
        for item in result["investigation_history"]
        if item["tool"].startswith("github_")
    ]

    assert github_history

    github_tools = {
        item["tool"]
        for item in github_history
    }

    assert "github_get_recent_commits" in github_tools

    # --------------------------------------------------------------
    # GitHub should not be recorded as a connection failure.
    # --------------------------------------------------------------

    github_failures = [
        failure
        for failure in result["failures"]
        if failure["source"] == "github"
    ]

    assert github_failures == []

@pytest.mark.asyncio
async def test_enterprise_workflow_human_review_approve(monkeypatch):

    global _tool_call_count
    _tool_call_count = 0

    # --------------------------------------------------------------
    # Mock MCP clients
    # --------------------------------------------------------------

    monkeypatch.setattr(
        "app.workflow.investigator.GitHubMCPClient",
        FakeGitHubClient,
    )

    monkeypatch.setattr(
        "app.workflow.investigator.JiraMCPClient",
        FakeJiraClient,
    )

    # --------------------------------------------------------------
    # Mock Gemini tool calling
    # --------------------------------------------------------------

    monkeypatch.setattr(
        GeminiClient,
        "generate_with_tools",
        fake_generate_with_tools,
    )

    # --------------------------------------------------------------
    # Force the Evaluator to request human review.
    #
    # Planner and Analysis can use the existing generic fake.
    # --------------------------------------------------------------

    def fake_hitl_generate_structured(
        self,
        prompt: str,
        response_schema,
    ):
        schema_name = response_schema.__name__

        if schema_name == "EvaluatorResult":
            return response_schema(
                evaluation_passed=False,
                confidence=0.55,
                reason=(
                    "Evidence is available, but the investigation "
                    "requires human approval before completion."
                ),
                evidence_sufficient=True,
                retry_required=False,
                human_review_required=True,
            )

        return fake_generate_structured(
            self,
            prompt,
            response_schema,
        )

    monkeypatch.setattr(
        GeminiClient,
        "generate_structured",
        fake_hitl_generate_structured,
    )

    monkeypatch.setattr(
        GroqClient,
        "generate_structured",
        fake_hitl_generate_structured,
    )

    monkeypatch.setattr(
        GroqClient,
        "generate",
        fake_generate,
    )

    # --------------------------------------------------------------
    # Initial workflow state
    # --------------------------------------------------------------

    initial_state = {
        "user_query": (
            "Analyze the current project status and "
            "identify potential delivery blockers."
        ),
        "project": "SCRUM",
        "plan": [],
        "required_sources": [],
        "github_data": {},
        "jira_data": {},
        "doc_data": {},
        "slack_data": {},
        "findings": [],
        "evidence": [],
        "investigation_history": [],
        "investigation_iteration": 0,
        "max_investigation_iterations": 5,
        "investigation_complete": False,
        "report": "",
        "confidence": 0.0,
        "human_review_required": False,
        "human_review_decision": "",
        "human_review_reason": "",
        "errors": [],
        "failures": [],
        "status": "",
        "evaluation_passed": False,
        "retry_count": 0,
        "max_retries": 2,
        "retry_required": False,
    }

    config = {
        "configurable": {
            "thread_id": "test-enterprise-workflow-hitl-approve",
        }
    }

    # --------------------------------------------------------------
    # First invocation must pause at human review.
    # --------------------------------------------------------------

    interrupted = await graph.ainvoke(
        initial_state,
        config=config,
    )

    assert interrupted["__interrupt__"]

    assert interrupted["human_review_required"] is True

    assert interrupted["evaluation_passed"] is False

    # --------------------------------------------------------------
    # Resume the SAME graph execution with human approval.
    # --------------------------------------------------------------

    result = await graph.ainvoke(
        Command(resume="approve"),
        config=config,
    )

    # --------------------------------------------------------------
    # Verify the human decision was persisted.
    # --------------------------------------------------------------

    assert result["human_review_decision"] == "approve"

    # --------------------------------------------------------------
    # Verify approval routed to report generation.
    # --------------------------------------------------------------

    assert result["status"] == "report_generated"

    assert result["report"]

    assert result["human_review_required"] is True

# ------------------------------------------------------------------
# Human review -> retry integration
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enterprise_workflow_human_review_retry(monkeypatch):

    global _tool_call_count
    _tool_call_count = 0

    # --------------------------------------------------------------
    # Mock MCP clients
    # --------------------------------------------------------------

    monkeypatch.setattr(
        "app.workflow.investigator.GitHubMCPClient",
        FakeGitHubClient,
    )

    monkeypatch.setattr(
        "app.workflow.investigator.JiraMCPClient",
        FakeJiraClient,
    )

    # --------------------------------------------------------------
    # Mock Gemini tool calling
    # --------------------------------------------------------------

    monkeypatch.setattr(
        GeminiClient,
        "generate_with_tools",
        fake_generate_with_tools,
    )

    # --------------------------------------------------------------
    # Evaluator behavior:
    #
    # First evaluation  -> human review
    # Second evaluation -> success after human retry
    # --------------------------------------------------------------

    evaluator_calls = 0

    def fake_hitl_retry_generate_structured(
        self,
        prompt: str,
        response_schema,
    ):
        nonlocal evaluator_calls

        if response_schema.__name__ == "EvaluatorResult":
            evaluator_calls += 1

            if evaluator_calls == 1:
                return response_schema(
                    evaluation_passed=False,
                    confidence=0.55,
                    reason=(
                        "Evidence requires additional investigation "
                        "before completion."
                    ),
                    evidence_sufficient=True,
                    retry_required=False,
                    human_review_required=True,
                )

            return response_schema(
                evaluation_passed=True,
                confidence=0.90,
                reason="Investigation completed successfully after retry.",
                evidence_sufficient=True,
                retry_required=False,
                human_review_required=False,
            )

        return fake_generate_structured(
            self,
            prompt,
            response_schema,
        )

    monkeypatch.setattr(
        GeminiClient,
        "generate_structured",
        fake_hitl_retry_generate_structured,
    )

    monkeypatch.setattr(
        GroqClient,
        "generate_structured",
        fake_hitl_retry_generate_structured,
    )

    monkeypatch.setattr(
        GroqClient,
        "generate",
        fake_generate,
    )

    # --------------------------------------------------------------
    # Initial workflow state
    # --------------------------------------------------------------

    initial_state = {
        "user_query": (
            "Analyze the current project status and "
            "identify potential delivery blockers."
        ),
        "project": "SCRUM",
        "plan": [],
        "required_sources": [],
        "github_data": {},
        "jira_data": {},
        "doc_data": {},
        "slack_data": {},
        "findings": [],
        "evidence": [],
        "investigation_history": [],
        "investigation_iteration": 0,
        "max_investigation_iterations": 5,
        "investigation_complete": False,
        "report": "",
        "confidence": 0.0,
        "human_review_required": False,
        "human_review_decision": "",
        "human_review_reason": "",
        "errors": [],
        "failures": [],
        "status": "",
        "evaluation_passed": False,
        "retry_count": 0,
        "max_retries": 2,
        "retry_required": False,
    }

    config = {
        "configurable": {
            "thread_id": "test-enterprise-workflow-hitl-retry",
        }
    }

    # --------------------------------------------------------------
    # First invocation must pause at human review.
    # --------------------------------------------------------------

    interrupted = await graph.ainvoke(
        initial_state,
        config=config,
    )

    assert interrupted["__interrupt__"]

    assert interrupted["human_review_required"] is True

    assert interrupted["evaluation_passed"] is False

    # --------------------------------------------------------------
    # Human chooses retry.
    # --------------------------------------------------------------

    result = await graph.ainvoke(
        Command(resume="retry"),
        config=config,
    )

    # --------------------------------------------------------------
    # Retry must go back through the workflow and eventually succeed.
    # --------------------------------------------------------------

    assert result["human_review_decision"] == "retry"

    assert result["retry_count"] == 1

    assert result["evaluation_passed"] is True

    assert result["human_review_required"] is False

    assert result["retry_required"] is False

    assert result["status"] == "report_generated"

    assert result["report"]

    assert evaluator_calls == 2