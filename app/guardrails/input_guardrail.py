from app.state.state import EnterpriseState


MAX_QUERY_LENGTH = 2000
MIN_QUERY_LENGTH = 10


class InputGuardrailError(ValueError):
    """Raised when a user request fails input validation."""


def validate_input(state: EnterpriseState) -> EnterpriseState:
    """
    Validate and normalize the incoming enterprise investigation request.
    """

    query = state.get("user_query", "")

    if not isinstance(query, str):
        raise InputGuardrailError(
            "Investigation request must be a string."
        )

    query = query.strip()

    if not query:
        raise InputGuardrailError(
            "Investigation request cannot be empty."
        )

    if len(query) < MIN_QUERY_LENGTH:
        raise InputGuardrailError(
            "Investigation request is too short."
        )

    if len(query) > MAX_QUERY_LENGTH:
        raise InputGuardrailError(
            "Investigation request exceeds the maximum allowed length."
        )

    state["user_query"] = query

    return state