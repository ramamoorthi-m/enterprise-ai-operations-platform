from app.workflow.graph import graph

initial_state = {
    "user_query": "Why is Project Alpha delayed?",
    "plan": [],
    "github_data": "",
    "documentation": "",
    "report": "",
    "confidence": 0.0,
    "status": "started",
}

result = graph.invoke(initial_state)

print(result)