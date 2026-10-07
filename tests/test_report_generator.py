from app.agents.report_generator import ReportGeneratorAgent
from app.llm.groq_client import GroqClient


def fake_generate(self, prompt: str):
    return """
# Enterprise Project Investigation Report

## Investigation Request
Project: SCRUM
Analyze the current project status and identify potential delivery blockers.

## Executive Summary
The project shows active development.

## Key Findings
- Jira has outstanding work.
- GitHub shows recent development activity.

## Risks
- Deployment status is unavailable.

## Evidence Gaps
- No deployment information was retrieved.

## Confidence
0.7
"""


def test_report_generator(monkeypatch):

    monkeypatch.setattr(
        GroqClient,
        "generate",
        fake_generate,
    )

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
    assert "active development" in report.lower()
    assert "Jira" in report
    assert "GitHub" in report
    assert "deployment" in report.lower()