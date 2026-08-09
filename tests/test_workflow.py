from app.workflow.graph import graph


def test_enterprise_workflow():
    initial_state = {
        "user_query": "Why is Project Alpha delayed?",
        "project": "Project Alpha",
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
        "status": "",
        "evaluation_passed": False,
        "retry_count": 0,
        "max_retries": 2,
    }

    result = graph.invoke(initial_state)

    print("\nFINAL STATE:")
    print(result)

    assert result["status"] == "report_generated"
    assert result["report"]
    assert result["findings"]

    assert result["evaluation_passed"] is True
    assert result["confidence"] > 0
    assert result["required_sources"]

    assert "GitHub" in result["report"]
    assert "Jira" in result["report"]