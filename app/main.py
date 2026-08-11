from app.workflow.graph import graph


initial_state = {
    "user_query": "Analyze the current status of my GitHub repository.",
    "project": "enterprise-ai-operations-platform",
    "plan": [],
    "required_sources": [],
    "github_data": {},
    "jira_data": {},
    "doc_data": {},
    "slack_data": {},
    "findings": [],
    "report": "",
    "confidence": 0.0,
    "human_review_required": False,
    "errors": [],
    "status": "started",
    "evaluation_passed": False,
    "retry_count": 0,
    "max_retries": 2,
}


result = graph.invoke(initial_state)

print(result)