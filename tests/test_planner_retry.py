import pytest

from app.llm.client import GeminiClient
from app.workflow.planner import planner
from app.state.plan import InvestigationPlan


def test_planner_creates_revised_plan_on_retry(monkeypatch):

    captured_prompt = {}

    def fake_generate_structured(
        self,
        prompt,
        response_schema,
    ):
        captured_prompt["value"] = prompt

        return InvestigationPlan(
            project="SCRUM",
            goal=(
                "Identify project delivery blockers "
                "with missing evidence addressed."
            ),
            tasks=[
                {
                    "description": (
                        "Inspect GitHub deployment status "
                        "because it was missing from the previous investigation."
                    ),
                    "source": "github",
                },
                {
                    "description": (
                        "Inspect recent GitHub commits "
                        "to establish current development activity."
                    ),
                    "source": "github",
                },
            ],
            required_sources=["github"],
        )

    monkeypatch.setattr(
        GeminiClient,
        "generate_structured",
        fake_generate_structured,
    )

    state = {
        "user_query": (
            "Analyze the current project status "
            "and identify potential delivery blockers."
        ),

        "project": "SCRUM",

        "retry_count": 1,

        "plan": [
            {
                "description": (
                    "Find overdue Jira issues and blocked tasks"
                ),
                "source": "jira",
            },
            {
                "description": (
                    "Inspect recent GitHub commits "
                    "and deployment status"
                ),
                "source": "github",
            },
        ],

        "required_sources": [
            "jira",
            "github",
        ],

        "findings": [
            "Jira contains one overdue task."
        ],

        "analysis": {
            "summary": (
                "The investigation identified Jira activity "
                "but lacked GitHub deployment evidence."
            ),
            "key_findings": [
                "One overdue Jira task was identified."
            ],
            "risks": [],
            "evidence_gaps": [
                "GitHub deployment status was not collected."
            ],
            "confidence": 0.55,
        },

        "errors": [],
    }

    result = planner(state)

    prompt = captured_prompt["value"]

    # ---------------------------------------------------------
    # Verify retry context reached the Planner
    # ---------------------------------------------------------

    assert "investigation retry attempt" in prompt.lower()

    assert "Previous investigation plan" in prompt

    assert "Previous findings" in prompt

    assert "Previous analysis" in prompt

    assert "Previous errors" in prompt

    assert "GitHub deployment status was not collected" in prompt

    # ---------------------------------------------------------
    # Verify Planner produced a revised plan
    # ---------------------------------------------------------

    assert result["status"] == "planning_completed"

    assert result["required_sources"] == ["github"]

    assert len(result["plan"]) == 2

    assert any(
        "deployment status" in task["description"].lower()
        for task in result["plan"]
    )

    # The revised plan should specifically target GitHub.
    assert all(
        task["source"] == "github"
        for task in result["plan"]
    )