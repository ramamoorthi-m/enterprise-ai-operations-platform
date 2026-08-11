import os

from app.llm.client import GeminiClient
from app.state.plan import InvestigationPlan, InvestigationTask


def test_llm_planner(monkeypatch):

    repository = (
        f"{os.getenv('GITHUB_OWNER')}/"
        f"{os.getenv('GITHUB_REPO')}"
    )

    def fake_generate_structured(self, prompt, response_schema):
        return InvestigationPlan(
            project=repository,
            goal="Analyze the current repository status and identify potential delivery blockers.",
            tasks=[
                InvestigationTask(
                    description="Inspect GitHub repository issues and recent development activity",
                    source="github",
                ),
                InvestigationTask(
                    description="Inspect Jira issues and blocked or overdue tasks",
                    source="jira",
                ),
            ],
            required_sources=["github", "jira"],
        )

    monkeypatch.setattr(
        GeminiClient,
        "generate_structured",
        fake_generate_structured,
    )

    llm = GeminiClient()

    query = (
        "Analyze the current repository status "
        "and identify potential delivery blockers."
    )

    plan = llm.generate_structured(
        prompt=query,
        response_schema=InvestigationPlan,
    )

    print("\nGenerated plan:")
    print(plan.model_dump_json(indent=2))

    assert plan.goal
    assert plan.project == repository
    assert plan.tasks
    assert plan.required_sources

    for task in plan.tasks:
        assert task.source in {"github", "jira"}