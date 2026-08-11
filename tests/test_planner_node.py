from app.llm.client import GeminiClient
from app.state.plan import InvestigationPlan
from app.workflow.planner import planner


def test_planner_node(monkeypatch):

    fake_plan = InvestigationPlan(
        project="Project Alpha",
        goal="Analyze the current project status and identify potential delivery blockers.",
        tasks=[
            {
                "description": "Find overdue Jira issues and blocked tasks",
                "source": "jira",
            },
            {
                "description": "Inspect recent GitHub commits and pull requests",
                "source": "github",
            },
        ],
        required_sources=["jira", "github"],
    )

    def fake_generate_structured(self, prompt, response_schema):
        return fake_plan

    monkeypatch.setattr(
        GeminiClient,
        "generate_structured",
        fake_generate_structured,
    )

    state = {
        "user_query": "Analyze the current project status and identify potential delivery blockers."
    }

    result = planner(state)

    print("\nPlanner node result:")
    print(result)

    assert result["status"] == "planning_completed"
    assert len(result["plan"]) > 0
    assert len(result["required_sources"]) > 0

    for source in result["required_sources"]:
        assert source in {"github", "jira"}