from app.workflow.graph import graph

initial_state = {
    "user_query": "Why is project alpha delayed?",
    "plan": [],
    "github_data": {},
    "jira_data": {},
    "findings": [],
    "report": "",
    "confidence": 0.0,
    "status": "started",
    "errors": [],
    "evaluation_passed": False,
    "retry_count": 0,
    "max_retries": 2,
}

result = graph.invoke(initial_state)

print(result)