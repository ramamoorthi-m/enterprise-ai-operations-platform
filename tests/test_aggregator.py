from app.workflow.aggregator import aggregator


def test_aggregator_normalizes_investigation_history():

    state = {
        "findings": [
            "Jira contains overdue work."
        ],
        "investigation_history": [
            {
                "iteration": 1,
                "tool": "github_get_recent_commits",
                "arguments": {
                    "repository": "ramamoorthi-m/enterprise-ai-operations-platform"
                },
                "result": {
                    "latest_commit_sha": "test-sha",
                    "latest_commit_message": "Test commit",
                },
            },
            {
                "iteration": 1,
                "tool": "jira_get_overdue_tasks",
                "arguments": {
                    "project": "SCRUM"
                },
                "result": {
                    "project": "SCRUM",
                    "overdue_tasks": [],
                },
            },
        ],
    }

    result = aggregator(state)

    print("\nAggregator result:")
    print(result)

    assert result["status"] == "evidence_collected"

    assert len(result["evidence"]) == 2

    github_evidence = result["evidence"][0]
    assert github_evidence["source"] == "github"
    assert github_evidence["tool"] == "github_get_recent_commits"
    assert github_evidence["status"] == "success"

    jira_evidence = result["evidence"][1]
    assert jira_evidence["source"] == "jira"
    assert jira_evidence["tool"] == "jira_get_overdue_tasks"
    assert jira_evidence["status"] == "success"

    assert result["findings"] == [
        "Jira contains overdue work."
    ]