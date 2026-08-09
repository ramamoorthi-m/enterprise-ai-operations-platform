from app.workflow.github_collector import github_collector


def test_github_collector():

    state = {
        "project": "Project Alpha"
    }

    result = github_collector(state)

    print("\nCollector result:")
    print(result)

    assert result["status"] == "github_collection_completed"

    assert result["github_data"]["repository"] == "Project Alpha"

    assert result["github_data"]["open_issues"] == 5

    assert result["github_data"]["latest_commit_days_ago"] == 2

    assert result["github_data"]["deployment_status"] == "failed"