from app.state.state import EnterpriseState


def route_after_planner(state: EnterpriseState) -> str:

    required_sources = state["required_sources"]

    if "github" in required_sources:
        return "github"

    if "jira" in required_sources:
        return "jira"

    return "end"

def route_after_github(state: EnterpriseState) -> str:
    required_sources = state.get("required_sources", [])

    if "jira" in required_sources:
        return "jira"

    return "aggregator"

def route_after_evaluation(state):

    if state.get("evaluation_passed"):
        return "success"

    if state.get("retry_required"):
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 2)

        if retry_count < max_retries:
            return "retry"

    return "failed"