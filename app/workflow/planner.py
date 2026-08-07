from app.state.state import EnterpriseState


def planner(state: EnterpriseState):

    query = state["user_query"].lower()

    required_sources = []

    if "github" in query or "code" in query or "repository" in query:
        required_sources.append("github")

    if "jira" in query or "ticket" in query or "task" in query:
        required_sources.append("jira")

    # Temporary fallback for broad investigation questions
    if not required_sources:
        required_sources = ["github", "jira"]

    plan = [
        f"Collect evidence from {source}"
        for source in required_sources
    ]

    return {
        "plan": plan,
        "required_sources": required_sources,
        "status": "planning_completed",
    }