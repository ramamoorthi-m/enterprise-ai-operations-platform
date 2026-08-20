from app.state.state import EnterpriseState

def retry_handler(state: EnterpriseState):

    current_retry = state.get("retry_count", 0)

    print(
        f"\n[RETRY HANDLER] BEFORE: retry_count={current_retry}"
    )

    result = {
        "retry_count": current_retry + 1,
        "status": "retrying",
    }

    print(
        f"[RETRY HANDLER] AFTER: retry_count={result['retry_count']}"
    )

    return result