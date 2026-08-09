from app.workflow.aggregator import aggregator


def test_aggregator():

    state = {
        "github_data": {
            "repository": "Project Alpha",
            "open_issues": 5,
            "latest_commit_days_ago": 2,
            "deployment_status": "failed",
        },
        "jira_data": {
            "project": "Project Alpha",
            "open_tasks": 8,
            "blocked_tasks": 3,
            "overdue_tasks": 2,
            "current_sprint": "Sprint 14",
        },
    }

    result = aggregator(state)

    print("\nAggregator result:")
    print(result)

    assert result["status"] == "evidence_collected"

    assert len(result["findings"]) == 2

    assert "GitHub:" in result["findings"][0]
    assert "Jira:" in result["findings"][1]