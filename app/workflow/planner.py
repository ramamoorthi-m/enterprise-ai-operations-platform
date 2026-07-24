from app.state.state import EnterpriseState


def planner(state: EnterpriseState):
    plan = [
        "Check GitHub repository",
        "Check project documentation",
        "Generate investigation report",
    ]

    return {
        "plan": plan,
        "status": "planning_completed",
    }