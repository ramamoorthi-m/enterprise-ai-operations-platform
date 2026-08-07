from app.state.state import EnterpriseState


def aggregator(state: EnterpriseState):
    findings = []

    github_data = state.get("github_data", {})
    jira_data = state.get("jira_data", {})

    if github_data:
        findings.append(
            f"GitHub: {github_data}"
        )

    if jira_data:
        findings.append(
            f"Jira: {jira_data}"
        )

    return {
        "findings": findings,
        "status": "evidence_collected",
    }