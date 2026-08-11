from typing import TypedDict, Any
class EnterpriseState(TypedDict, total=False):
    user_query: str
    project: str
    plan: list[dict[str, str]]
    required_sources: list[str]

    github_repository: str
    jira_project_key: str

    github_data: dict[str, Any]
    jira_data: dict[str, Any]
    doc_data: dict[str, Any]
    slack_data: dict[str, Any]

    findings:list[dict[str, Any]]
    analysis: str
    report: str
    confidence: float
    human_review_required: bool
    errors: list[str]

    status: str

    evaluation_passed: bool
    retry_count: int
    max_retries: int

    investigation_history: list[dict[str, Any]]
    investigation_iteration: int
    max_investigation_iterations: int
    investigation_complete: bool
