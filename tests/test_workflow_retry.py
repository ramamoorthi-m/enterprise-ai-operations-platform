import pytest

from app.llm.client import GeminiClient
from app.llm.groq_client import GroqClient
from app.workflow.graph import graph
from app.state.analysis import AnalysisResult
from app.state.plan import InvestigationPlan
from app.mcp.jira_client import JiraMCPClient
from app.mcp.github_client import GitHubMCPClient


class FakeRetryTracker:
    planner_calls = 0
    investigation_calls = 0
    evaluator_calls = 0
    github_calls = 0
    jira_calls = 0


class FakeFunctionCall:
    def __init__(self, name, args):
        self.name = name
        self.args = args

class FakeToolResponse:
    def __init__(
        self,
        function_calls=None,
        text="",
    ):
        self.function_calls = function_calls or []
        self.text = text

        parts = []

        for function_call in self.function_calls:
            parts.append(
                type(
                    "FakePart",
                    (),
                    {
                        "function_call": function_call,
                    },
                )()
            )

        self.candidates = [
            type(
                "FakeCandidate",
                (),
                {
                    "content": type(
                        "FakeContent",
                        (),
                        {
                            "parts": parts,
                        },
                    )()
                },
            )()
        ]

def reset_tracker():
    FakeRetryTracker.planner_calls = 0
    FakeRetryTracker.investigation_calls = 0
    FakeRetryTracker.evaluator_calls = 0
    FakeRetryTracker.github_calls = 0
    FakeRetryTracker.jira_calls = 0


@pytest.mark.asyncio
async def test_workflow_retry_and_replanning(monkeypatch):
    reset_tracker()

    # =========================================================
    # Fake MCP lifecycle
    #
    # The real MCP servers must NOT be contacted during tests.
    # =========================================================

    async def fake_jira_connect(self):
        return None

    async def fake_jira_close(self):
        return None

    async def fake_github_connect(self):
        return None

    async def fake_github_close(self):
        return None

    monkeypatch.setattr(
        JiraMCPClient,
        "connect",
        fake_jira_connect,
    )

    monkeypatch.setattr(
        JiraMCPClient,
        "close",
        fake_jira_close,
    )

    monkeypatch.setattr(
        GitHubMCPClient,
        "connect",
        fake_github_connect,
    )

    monkeypatch.setattr(
        GitHubMCPClient,
        "close",
        fake_github_close,
    )

    # =========================================================
    # Fake structured LLM responses
    # =========================================================

    def fake_generate_structured(
        self,
        prompt,
        response_schema,
    ):
        schema_name = getattr(
            response_schema,
            "__name__",
            "",
        )

        # -----------------------------------------------------
        # Planner
        # -----------------------------------------------------
        if schema_name == "InvestigationPlan":
            FakeRetryTracker.planner_calls += 1

            # First planning attempt
            if FakeRetryTracker.planner_calls == 1:
                return InvestigationPlan(
                    project="SCRUM",
                    goal=(
                        "Analyze the current project status "
                        "and identify potential delivery blockers."
                    ),
                    tasks=[
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
                    required_sources=[
                        "jira",
                        "github",
                    ],
                )

            # -------------------------------------------------
            # Retry planning attempt
            #
            # The first investigation failed to collect the
            # required GitHub evidence.
            #
            # The replanner therefore focuses only on GitHub.
            # -------------------------------------------------
            return InvestigationPlan(
                project="SCRUM",
                goal="Collect missing deployment evidence.",
                tasks=[
                    {
                        "description": (
                            "Inspect GitHub deployment status"
                        ),
                        "source": "github",
                    }
                ],
                required_sources=["github"],
            )

        # -----------------------------------------------------
        # Evaluator
        # -----------------------------------------------------
        if schema_name == "EvaluatorResult":
            FakeRetryTracker.evaluator_calls += 1

            # First evaluation:
            # insufficient evidence -> retry.
            if FakeRetryTracker.evaluator_calls == 1:
                return {
                    "evaluation_passed": False,
                    "confidence": 0.45,
                    "reason": (
                        "The investigation is incomplete because "
                        "GitHub deployment evidence is missing."
                    ),
                    "evidence_sufficient": False,
                    "retry_required": True,
                    "human_review_required": False,
                }

            # Second evaluation:
            # GitHub evidence is now available.
            return {
                "evaluation_passed": True,
                "confidence": 0.9,
                "reason": (
                    "The required GitHub deployment evidence "
                    "was collected successfully."
                ),
                "evidence_sufficient": True,
                "retry_required": False,
                "human_review_required": False,
            }

        # -----------------------------------------------------
        # Analysis
        # -----------------------------------------------------
        if schema_name == "AnalysisResult":
            return AnalysisResult(
                summary=(
                    "The investigation collected the required "
                    "deployment evidence."
                ),
                key_findings=[
                    "GitHub deployment status was retrieved."
                ],
                risks=[],
                evidence_gaps=[],
                confidence=0.85,
                assessment=(
                    "The available evidence is sufficient to assess "
                    "the current project status."
                ),
            )

        # -----------------------------------------------------
        # Report
        # -----------------------------------------------------
        if schema_name == "ReportResult":
            return {
                "report": (
                    "The project investigation completed "
                    "successfully after retrying the missing "
                    "GitHub evidence collection."
                )
            }

        raise AssertionError(
            f"Unexpected structured schema: {schema_name}"
        )

    monkeypatch.setattr(
        GroqClient,
        "generate_structured",
        fake_generate_structured,
    )

    monkeypatch.setattr(
        GeminiClient,
        "generate_structured",
        fake_generate_structured,
    )

    # =========================================================
    # Fake investigation LLM tool-call generation
    # =========================================================
    #
    # First investigation:
    #
    #   LLM call 1
    #       -> Jira overdue tool
    #
    #   Jira tool fails
    #
    #   LLM call 2
    #       -> text response
    #
    #   Investigation terminates with errors.
    #
    # Retry investigation:
    #
    #   LLM call 3
    #       -> GitHub deployment tool
    #
    #   GitHub tool succeeds
    #
    #   LLM call 4
    #       -> completion text
    #
    # =========================================================

    def fake_generate_with_tools(
        self,
        contents,
        tools,
        force_tool_call=False,
    ):
        FakeRetryTracker.investigation_calls += 1

        # -----------------------------------------------------
        # First investigation attempt
        # -----------------------------------------------------
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

        # -----------------------------------------------------
        # First investigation terminates after Jira failure.
        # -----------------------------------------------------
        if FakeRetryTracker.investigation_calls == 2:
            return FakeToolResponse(
                function_calls=[],
                text=(
                    "Jira investigation failed. "
                    "GitHub deployment evidence was not collected."
                ),
            )

        # -----------------------------------------------------
        # Retry investigation
        # -----------------------------------------------------
        if FakeRetryTracker.investigation_calls == 3:
            return FakeToolResponse(
                function_calls=[
                    FakeFunctionCall(
                        name="github_get_deployment_status",
                        args={
                            "repository": (
                                "ramamoorthi-m/"
                                "enterprise-ai-operations-platform"
                            )
                        },
                    )
                ]
            )

        # -----------------------------------------------------
        # Retry investigation completes successfully.
        # -----------------------------------------------------
        return FakeToolResponse(
            function_calls=[],
            text=(
                "GitHub deployment evidence collected. "
                "Investigation completed."
            ),
        )

    monkeypatch.setattr(
        GeminiClient,
        "generate_with_tools",
        fake_generate_with_tools,
    )

    # =========================================================
    # Fake Jira tool execution
    #
    # First Jira call fails intentionally.
    # =========================================================

    async def fake_get_overdue_tasks(
        self,
        project,
    ):
        FakeRetryTracker.jira_calls += 1

        raise RuntimeError(
            "Simulated Jira connection failure"
        )

    monkeypatch.setattr(
        JiraMCPClient,
        "get_overdue_tasks",
        fake_get_overdue_tasks,
    )

    # ---------------------------------------------------------
    # This should not be called in the first attempt because
    # the overdue-task call fails and the investigation exits.
    # ---------------------------------------------------------

    async def fake_get_blocked_tasks(
        self,
        project,
    ):
        return {
            "project": project,
            "blocked_tasks": 0,
        }

    monkeypatch.setattr(
        JiraMCPClient,
        "get_blocked_tasks",
        fake_get_blocked_tasks,
    )

    # ---------------------------------------------------------
    # Other Jira tools are also made safe for the test.
    # ---------------------------------------------------------

    async def fake_get_open_tasks(
        self,
        project,
    ):
        return {
            "project": project,
            "open_tasks": 0,
        }

    async def fake_get_current_sprint(
        self,
        project,
    ):
        return {
            "project": project,
            "sprint": None,
        }

    monkeypatch.setattr(
        JiraMCPClient,
        "get_open_tasks",
        fake_get_open_tasks,
    )

    monkeypatch.setattr(
        JiraMCPClient,
        "get_current_sprint",
        fake_get_current_sprint,
    )

    # =========================================================
    # Fake GitHub deployment tool execution
    # =========================================================

    async def fake_get_deployment_status(
        self,
        repository,
    ):
        FakeRetryTracker.github_calls += 1

        return {
            "repository": repository,
            "deployment_status": "success",
        }

    monkeypatch.setattr(
        GitHubMCPClient,
        "get_deployment_status",
        fake_get_deployment_status,
    )

    # ---------------------------------------------------------
    # Make other GitHub tools safe as well.
    # ---------------------------------------------------------

    async def fake_get_repository_issues(
        self,
        repository,
    ):
        return {
            "repository": repository,
            "issues": [],
        }

    async def fake_get_recent_commits(
        self,
        repository,
    ):
        return {
            "repository": repository,
            "commits": [],
        }

    monkeypatch.setattr(
        GitHubMCPClient,
        "get_repository_issues",
        fake_get_repository_issues,
    )

    monkeypatch.setattr(
        GitHubMCPClient,
        "get_recent_commits",
        fake_get_recent_commits,
    )

    # =========================================================
    # Initial workflow state
    # =========================================================

    initial_state = {
        "user_query": (
            "Analyze the current project status "
            "and identify potential delivery blockers."
        ),
        "retry_count": 0,
        "max_retries": 2,
        "failures": [],
        "errors": [],
        "findings": [],
        "investigation_history": [],
        "investigation_iteration": 0,
    }

    # =========================================================
    # Run workflow asynchronously
    # =========================================================

    result = await graph.ainvoke(
        initial_state,
        config={
            "configurable": {
                "thread_id": "test-retry-workflow-fresh",
            }
        },
    )

    print("\n===== FINAL RESULT =====")
    print(result)

    print("\n===== TRACKER =====")
    print("planner_calls =", FakeRetryTracker.planner_calls)
    print("evaluator_calls =", FakeRetryTracker.evaluator_calls)
    print("investigation_calls =", FakeRetryTracker.investigation_calls)
    print("jira_calls =", FakeRetryTracker.jira_calls)
    print("github_calls =", FakeRetryTracker.github_calls)




    assert result["status"] == "report_generated"

    assert result["retry_count"] == 1

    assert FakeRetryTracker.planner_calls == 2

    assert FakeRetryTracker.evaluator_calls == 2

    assert FakeRetryTracker.jira_calls == 1

    assert FakeRetryTracker.github_calls == 1

    # =========================================================
    # Verify replanning
    # =========================================================

    assert result["required_sources"] == ["github"]

    assert result["plan"]

    assert all(
        task["source"] == "github"
        for task in result["plan"]
    )

    # =========================================================
    # Verify investigation history
    # =========================================================

    history = result["investigation_history"]

    assert len(history) == 2

    # First attempt: Jira failed.
    assert history[0]["tool"] == (
        "jira_get_overdue_tasks"
    )

    assert history[0]["iteration"] == 1

    assert history[0]["result"]["error"]

    # Retry attempt: GitHub succeeded.
    assert history[1]["tool"] == (
        "github_get_deployment_status"
    )

    assert history[1]["iteration"] == 3

    assert not history[1]["result"].get(
        "error"
    )

    # =========================================================
    # Verify failure preservation
    # =========================================================

    failures = result["failures"]

    assert failures

    jira_failure = next(
        failure
        for failure in failures
        if failure["tool"] == "jira_get_overdue_tasks"
    )

    assert jira_failure["category"] == (
        "tool_execution_failure"
    )

    assert jira_failure["retryable"] is True

    # =========================================================
    # Verify evidence
    # =========================================================

    evidence = result["evidence"]

    assert len(evidence) == 2

    assert evidence[0]["source"] == "jira"

    assert evidence[0]["status"] == "failed"

    assert evidence[1]["source"] == "github"

    assert evidence[1]["status"] == "success"

    # =========================================================
    # Verify final evaluator state
    # =========================================================

    assert result["evaluation_passed"] is True

    assert result["confidence"] >= 0.0

    assert result["human_review_required"] is False

    assert result["retry_required"] is False

    # =========================================================
    # Verify global investigation iteration
    #
    # First attempt:
    #   1 -> Jira tool call
    #   2 -> investigation completion
    #
    # Retry:
    #   3 -> GitHub tool call
    #   4 -> investigation completion
    #
    # =========================================================

    assert result["investigation_iteration"] == 4

    # =========================================================
    # Verify final report
    # =========================================================

    assert result["report"]

    assert (
        "GitHub deployment evidence"
        in result["report"]
    )