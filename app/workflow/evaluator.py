from app.state.state import EnterpriseState


def evaluator(state: EnterpriseState):

    required_sources = state.get("required_sources", [])

    github_data = state.get("github_data", {})
    jira_data = state.get("jira_data", {})

    evidence_complete = True

    if "github" in required_sources and not github_data:
        evidence_complete = False

    if "jira" in required_sources and not jira_data:
        evidence_complete = False

    if evidence_complete:
        return {
            "evaluation_passed": True,
            "confidence": 0.9,
            "status": "evaluation_passed",
        }

    return {
        "evaluation_passed": False,
        "confidence": 0.3,
        "status": "evaluation_failed",
    }