from app.workflow.github_collector import github_collector


class FakeTool:

    def __init__(self, result):
        self.result = result

    def invoke(self, args):
        return self.result


def test_github_collector(monkeypatch):

    monkeypatch.setattr(
        "app.workflow.github_collector.get_repository_issues",
        FakeTool(
            {
                "open_issues": 0,
            }
        ),
    )

    monkeypatch.setattr(
        "app.workflow.github_collector.get_recent_commits",
        FakeTool(
            {
                "latest_commit_sha": "test-sha",
                "latest_commit_message": "Test commit",
                "latest_commit_author": "test-author",
                "latest_commit_date": "2026-08-11T00:00:00Z",
            }
        ),
    )

    monkeypatch.setattr(
        "app.workflow.github_collector.get_deployment_status",
        FakeTool(
            {
                "deployment_status": "success",
            }
        ),
    )

    result = github_collector(
        {
            "project": "enterprise-ai-operations-platform",
        }
    )

    print("\nCollector result:")
    print(result)

    assert result["status"] == "github_collection_completed"

    github_data = result["github_data"]

    assert github_data["repository"]

    assert isinstance(
        github_data["repository"],
        str,
    )

    assert github_data["open_issues"] == 0

    assert github_data["latest_commit_sha"] == "test-sha"
    assert github_data["latest_commit_message"] == "Test commit"
    assert github_data["latest_commit_author"] == "test-author"
    assert github_data["latest_commit_date"] == "2026-08-11T00:00:00Z"

    assert github_data["deployment_status"] == "success"