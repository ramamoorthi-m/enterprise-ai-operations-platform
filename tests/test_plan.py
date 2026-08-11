from app.state.plan import InvestigationPlan


def test_investigation_plan():

    plan = InvestigationPlan(
        project="enterprise-ai-operations-platform",
        goal="Analyze the current status and identify potential delivery blockers",
        tasks=[
            {
                "description": "Find overdue Jira issues",
                "source": "jira",
            },
            {
                "description": "Inspect recent GitHub pull requests",
                "source": "github",
            },
        ],
        required_sources=["jira", "github"],
    )

    assert plan.project == "enterprise-ai-operations-platform"
    assert plan.goal == "Analyze the current status and identify potential delivery blockers"
    assert len(plan.tasks) == 2
    assert plan.required_sources == ["jira", "github"]