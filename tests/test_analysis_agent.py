from app.agents.analysis import AnalysisAgent
from app.llm.client import GeminiClient


def test_analysis_agent():

    state = {
        "user_query": (
            "Analyze the current project status "
            "and identify potential delivery blockers."
        ),
        "project": "SCRUM",

        "plan": [
            {
                "description": (
                    "Find overdue Jira issues and blocked tasks"
                ),
                "source": "jira",
            },
            {
                "description": (
                    "Inspect recent GitHub commits "
                    "and deployment status"
                ),
                "source": "github",
            },
        ],

        "required_sources": [
            "jira",
            "github",
        ],

        "github_data": {
            "get_recent_commits": {
                "repository": (
                    "ramamoorthi-m/"
                    "enterprise-ai-operations-platform"
                ),
                "latest_commit_sha": "test-sha",
                "latest_commit_message": (
                    "Implement LLM Planner and graph workflow"
                ),
                "latest_commit_author": "test-author",
                "latest_commit_date": (
                    "2026-08-11T00:00:00Z"
                ),
            }
        },

        "jira_data": {
            "get_overdue_tasks": {
                "project": "SCRUM",
                "overdue_tasks": 0,
            }
        },

        "doc_data": {},
        "slack_data": {},

        "findings": [
            (
                "Investigation completed. "
                "Jira shows no overdue tasks. "
                "GitHub shows recent development activity."
            )
        ],

        "investigation_history": [
            {
                "iteration": 1,
                "tool": "get_overdue_tasks",
                "arguments": {
                    "project": "SCRUM"
                },
                "result": {
                    "project": "SCRUM",
                    "overdue_tasks": 0,
                },
            },
            {
                "iteration": 1,
                "tool": "get_recent_commits",
                "arguments": {
                    "repository": (
                        "ramamoorthi-m/"
                        "enterprise-ai-operations-platform"
                    )
                },
                "result": {
                    "repository": (
                        "ramamoorthi-m/"
                        "enterprise-ai-operations-platform"
                    ),
                    "latest_commit_sha": "test-sha",
                    "latest_commit_message": (
                        "Implement LLM Planner and graph workflow"
                    ),
                },
            },
        ],
    }

    llm = GeminiClient()

    agent = AnalysisAgent(
        llm=llm,
    )

    result = agent.analyze(state)

    print("\nAnalysis result:")
    print(result.model_dump())

    assert result.summary
    assert len(result.key_findings) > 0
    assert 0.0 <= result.confidence <= 1.0