from app.state.plan import InvestigationPlan


def test_investigation_plan():
    plan = InvestigationPlan(
        goal="Determine why Project Alpha is delayed",
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

    assert plan.goal == "Determine why Project Alpha is delayed"
    assert len(plan.tasks) == 2
    assert plan.tasks[0].source == "jira"