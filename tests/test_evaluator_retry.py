from app.agents.evaluator import (
    EvaluatorAgent,
    EvaluatorResult,
)


class FakeEvaluatorLLM:

    def generate_structured(self, prompt, response_schema):
        return EvaluatorResult(
            evaluation_passed=False,
            confidence=0.55,
            reason=(
                "GitHub evidence required by the investigation plan "
                "was not collected. Additional investigation is needed."
            ),
            evidence_sufficient=False,
            retry_required=True,
            human_review_required=False,
        )


def test_evaluator_detects_missing_github_evidence():

    llm = FakeEvaluatorLLM()

    agent = EvaluatorAgent(llm=llm)

    state = {
        "user_query": (
            "Analyze the current project status "
            "and identify potential delivery blockers."
        ),

        "project": "SCRUM",

        # Planner required both systems.
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

        # Jira evidence exists.
        "jira_data": {
            "jira_get_overdue_tasks": {
                "project": "SCRUM",
                "overdue_tasks": 1,
            }
        },

        # GitHub evidence is intentionally missing.
        "github_data": {},

        "findings": [
            "Jira contains one overdue task."
        ],

        "investigation_history": [
            {
                "iteration": 1,
                "tool": "jira_get_overdue_tasks",
                "arguments": {
                    "project": "SCRUM"
                },
                "result": {
                    "project": "SCRUM",
                    "overdue_tasks": 1,
                },
            }
        ],

        "analysis": {
            "summary": "One overdue Jira task was identified.",
            "key_findings": [
                "Jira contains one overdue task."
            ],
            "risks": [],
            "evidence_gaps": [
                "GitHub evidence was not collected."
            ],
            "confidence": 0.55,
        },
    }

    result = agent.evaluate(state)

    assert result["evaluation_passed"] is False

    assert result["evidence_sufficient"] is False

    assert result["retry_required"] is True

    assert result["human_review_required"] is False

    assert result["confidence"] < 1.0

    assert "GitHub" in result["reason"]