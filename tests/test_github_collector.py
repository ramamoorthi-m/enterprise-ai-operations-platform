import os

from app.workflow.github_collector import github_collector


def test_github_collector():

    state = {
        "project": os.getenv(
            "GITHUB_REPO",
            "enterprise-ai-operations-platform",
        )
    }

    result = github_collector(state)

    print("\nCollector result:")
    print(result)

    assert result["status"] == "github_collection_completed"

    github_data = result["github_data"]

    assert github_data["repository"]
    assert isinstance(github_data["repository"], str)

    assert "open_issues" in github_data
    assert "latest_commit_sha" in github_data
    assert "latest_commit_message" in github_data
    assert "latest_commit_author" in github_data
    assert "latest_commit_date" in github_data
    assert "deployment_status" in github_data