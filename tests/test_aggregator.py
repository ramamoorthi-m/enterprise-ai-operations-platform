import os

from app.workflow.aggregator import aggregator


def test_aggregator():

    repository = (
        f"{os.getenv('GITHUB_OWNER')}/"
        f"{os.getenv('GITHUB_REPO')}"
    )

    state = {
        "findings": [],
        "github_data": {
            "repository": repository,
            "open_issues": 0,
            "latest_commit_sha": "test-sha",
            "latest_commit_message": "Test commit",
            "latest_commit_author": "test-author",
            "latest_commit_date": "2026-08-11T00:00:00Z",
            "deployment_status": "no_workflow_runs_found",
        },
        "jira_data": {},
    }

    result = aggregator(state)

    print("\nAggregator result:")
    print(result)

    assert result["status"] == "evidence_collected"

    assert len(result["findings"]) == 1
    assert "GitHub:" in result["findings"][0]
    assert repository in result["findings"][0]