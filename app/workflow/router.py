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

def route_after_evaluation(state: EnterpriseState) -> str:

    if state.get("human_review_required"):
        return "human_review"
    
    if state.get("evaluation_passed"):
        return "success"
    

    if state.get("retry_required"):
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 2)

        if retry_count < max_retries:
            return "retry"

    return "failed"

def route_after_human_review(state: EnterpriseState) -> str:
    decision = state.get("human_review_decision")

    if decision =="approve":
        return "success"

    if decision == "retry":
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 2)

        if retry_count < max_retries:
            return "retry"

    return "failed"