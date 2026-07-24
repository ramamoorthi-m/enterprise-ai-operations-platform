from typing import TypedDict
class EnterpriseState(TypedDict):
    user_query: str
    plan: list[str]
    status: str
    findings: list[str]
    report: str
    confidence: float
    human_review_required: bool
    errors: list[str]