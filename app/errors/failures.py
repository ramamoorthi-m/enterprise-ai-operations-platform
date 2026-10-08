from typing import Any


CONNECTION_FAILURE = "connection_failure"
TOOL_EXECUTION_FAILURE = "tool_execution_failure"
INVALID_TOOL_CALL = "invalid_tool_call"
GUARDRAIL_BLOCKED = "guardrail_blocked"


def build_failure(
    *,
    category: str,
    source: str,
    message: str,
    retryable: bool,
    blocking: bool = True,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "category": category,
        "source": source,
        "message": message,
        "retryable": retryable,
        "blocking": blocking,
        **extra,
    }