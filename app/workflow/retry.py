from app.state.state import EnterpriseState


def retry_handler(state: EnterpriseState):

    current_retry = state.get("retry_count", 0)

    return {
        "retry_count": current_retry + 1,
        "status": "retrying",
    }