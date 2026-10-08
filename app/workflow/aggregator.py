from typing import Any

from app.state.state import EnterpriseState


def _build_evidence_item(
    item: dict[str, Any],
) -> dict[str, Any]:
    tool_name = item.get("tool", "")
    result = item.get("result")

    # Every investigation history item starts as a successful
    # execution candidate. Errors or guardrail blocks override this.
    status = "success"

    if isinstance(result, dict):
        if result.get("guardrail_blocked"):
            status = "blocked"

        elif result.get("error"):
            status = "failed"

    source = "unknown"

    if tool_name.startswith("github_"):
        source = "github"

    elif tool_name.startswith("jira_"):
        source = "jira"

    evidence_item = {
        "iteration": item.get("iteration"),
        "source": source,
        "tool": tool_name,
        "arguments": item.get("arguments", {}),
        "status": status,
        "result": result,
    }

    # Preserve the structured failure classification when one exists.
    if (
        isinstance(result, dict)
        and result.get("failure_category")
    ):
        evidence_item["failure_category"] = (
            result["failure_category"]
        )

    return evidence_item


def aggregator(state: EnterpriseState):
    """Normalize investigation history into structured evidence."""

    history = state.get(
        "investigation_history",
        [],
    )

    evidence = [
        _build_evidence_item(item)
        for item in history
    ]

    findings = state.get(
        "findings",
        [],
    )

    return {
        "evidence": evidence,
        "findings": findings,
        "status": "evidence_collected",
    }