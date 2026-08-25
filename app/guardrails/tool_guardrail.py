from typing import Any


class ToolGuardrailError(ValueError):
    """Raised when a tool call violates execution constraints."""



REQUIRED_ARGUMENTS = {
    "jira_get_open_tasks": {"project"},
    "jira_get_blocked_tasks": {"project"},
    "jira_get_overdue_tasks": {"project"},
    "jira_get_current_sprint": {"project"},
    "github_get_repository_issues": {"repository"},
    "github_get_recent_commits": {"repository"},
    "github_get_deployment_status": {"repository"},
}


def validate_tool_call(
    tool_name: str,
    arguments: dict[str, Any],
    available_tools: dict[str, Any],
) -> None:
    """
    Validate an LLM-generated tool call before execution.
    """

    if not isinstance(tool_name, str) or not tool_name.strip():
        raise ToolGuardrailError(
            "Tool name must be a non-empty string."
        )

    if tool_name not in available_tools:
        raise ToolGuardrailError(
            f"Tool '{tool_name}' is not available."
        )

    if not isinstance(arguments, dict):
        raise ToolGuardrailError(
            "Tool arguments must be a dictionary."
        )

    

    required = REQUIRED_ARGUMENTS.get(
        tool_name,
        set(),
    )

    missing = required - arguments.keys()

    if missing:
        raise ToolGuardrailError(
            f"Tool '{tool_name}' is missing required "
            f"arguments: {sorted(missing)}"
        )