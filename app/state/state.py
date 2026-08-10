from typing import TypedDict
class EnterpriseState(TypedDict, total=False):
    user_query: str
    project: str
    plan: list[dict[str, str]]
    required_sources: list[str]

    github_repository: str
    jira_project_key: str

    github_data: dict[str, any]
    jira_data: dict[str, any]
    doc_data: dict[str, any]
    slack_data: dict[str, any]

    findings:list[str]
    report: str
    confidence: float
    human_review_required: bool
    errors: list[str]

    status: str

    evaluation_passed: bool
    retry_count: int
    max_retries: int