from app.tools import github_tools


class FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return [
            {
                "number": 101,
                "title": "Fix authentication issue",
            },
            {
                "number": 102,
                "title": "Improve agent workflow",
            },
        ]


def fake_get(*args, **kwargs):
    return FakeResponse()


def test_get_repository_issues(monkeypatch):
    monkeypatch.setattr(
        github_tools.requests,
        "get",
        fake_get,
    )

    result = github_tools.get_repository_issues.invoke({
        "repository": "ramamoorthi-m/enterprise-ai-operations-platform"
    })

    assert result["repository"] == (
        "ramamoorthi-m/enterprise-ai-operations-platform"
    )
    assert result["open_issues"] == 2