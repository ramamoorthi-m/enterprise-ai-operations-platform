from typing import Any

from app.state.state import EnterpriseState


def _build_evidence_item(
    item: dict[str, Any],
) -> dict[str, Any]:
    """Normalize one tool execution into a stable evidence record."""

    tool_name = item.get("tool", "")
    result = item.get("result")

    status = "success"

    if isinstance(result, dict) and result.get("error"):
        status = "failed"

    source = "unknown"

    if tool_name.startswith("github_"):
        source = "github"
    elif tool_name.startswith("jira_"):
        source = "jira"

    return {
        "iteration": item.get("iteration"),
        "source": source,
        "tool": tool_name,
        "arguments": item.get("arguments", {}),
        "status": status,
        "result": result,
    }


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