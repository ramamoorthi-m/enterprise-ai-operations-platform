from app.agents.report_generator import ReportGeneratorAgent


def test_report_generator():

    state = {
        "project": "SCRUM",
        "user_query": (
            "Analyze the current project status "
            "and identify potential delivery blockers."
        ),
        "analysis": {
            "summary": "The project shows active development.",
            "key_findings": [
                "Jira has outstanding work.",
                "GitHub shows recent development activity.",
            ],
            "risks": [
                "Deployment status is unavailable."
            ],
            "evidence_gaps": [
                "No deployment information was retrieved."
            ],
            "confidence": 0.7,
        },
        "findings": [],
        "confidence": 0.7,
    }

    agent = ReportGeneratorAgent()

    result = agent.generate(state)

    assert "report" in result
    assert result["status"] == "report_generated"

    report = result["report"]

    assert "Enterprise Project Investigation Report" in report
    assert "SCRUM" in report
    assert "The project shows active development." in report
    assert "Jira has outstanding work." in report
    assert "Deployment status is unavailable." in report
    assert "No deployment information was retrieved." in report