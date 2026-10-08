from unittest.mock import patch

from app.state.plan import InvestigationPlan
from app.workflow.planner import planner


def test_planner_uses_persistent_memory():
    captured_prompt = {}

    def fake_generate_structured(
        self,
        prompt,
        response_schema,
    ):
        captured_prompt["value"] = prompt

        return InvestigationPlan(
            project="SCRUM",
            goal="Assess current project status.",
            tasks=[
                {
                    "description": "Inspect blocked Jira tasks",
                    "source": "jira",
                }
            ],
            required_sources=["jira"],
        )

    state = {
        "user_query": "What is the current status of our operations?",
        "project": "SCRUM",
        "memory_context": [
            {
                "memory_type": "FACT",
                "content": "SCRUM is the production Jira project",
                "source": "jira",
                "confidence": 0.95,
                "importance": 0.9,
            }
        ],
        "retry_count": 0,
        "plan": [],
        "findings": [],
        "analysis": {},
        "errors": [],
    }

    with patch(
        "app.workflow.planner.GeminiClient.generate_structured",
        new=fake_generate_structured,
    ):
        result = planner(state)

    prompt = captured_prompt["value"]

    assert "PERSISTENT BUSINESS MEMORY" in prompt
    assert "SCRUM is the production Jira project" in prompt
    assert "[FACT]" in prompt
    assert "source: jira" in prompt

    assert result["project"] == "SCRUM"
    assert len(result["plan"]) == 1
    assert result["plan"][0]["source"] == "jira"