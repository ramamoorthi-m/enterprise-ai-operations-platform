from app.llm.client import GeminiClient
from app.state.plan import InvestigationPlan


def test_llm_planner(monkeypatch):

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

    llm = GeminiClient()

    query = "Analyze the current project status and identify potential delivery blockers."

    prompt = f"""
You are an enterprise investigation planning agent.

Analyze the user's request and create an investigation plan.

Available sources:
- GitHub: repositories, pull requests, commits, issues
- Jira: projects, tickets, sprint status, blockers

Rules:
- Only use github or jira.
- Do not invent information.
- Create concrete investigation tasks.
- Every task must specify a source.
- Focus on evidence collection.

User request:
{query}
"""

    plan = llm.generate_structured(
        prompt=prompt,
        response_schema=InvestigationPlan,
    )

    print("\nGenerated plan:")
    print(plan.model_dump_json(indent=2))

    assert plan.goal
    assert plan.project == "Project Alpha"
    assert plan.tasks
    assert plan.required_sources

    for task in plan.tasks:
        assert task.source in {"github", "jira"}