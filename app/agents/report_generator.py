from app.llm.groq_client import GroqClient
from app.state.state import EnterpriseState


class ReportGeneratorAgent:

    def __init__(self):
        self.llm = GroqClient(
            model="openai/gpt-oss-120b"
        )

    def generate(self, state: EnterpriseState):

        project = state.get("project", "Unknown Project")
        user_query = state.get("user_query", "")

        analysis = state.get("analysis", {})
        findings = state.get("findings", [])

        jira_data = state.get("jira_data", {})
        github_data = state.get("github_data", {})

        prompt = f"""
You are an enterprise project report generator.

Generate a concise, professional project investigation report
based ONLY on the evidence and analysis provided below.

Do not invent facts.
Do not infer evidence that was not collected.
Clearly distinguish confirmed findings from uncertainty.

PROJECT:
{project}

INVESTIGATION REQUEST:
{user_query}

ANALYSIS:
{analysis}

FINDINGS:
{findings}

JIRA EVIDENCE:
{jira_data}

GITHUB EVIDENCE:
{github_data}

Generate the report using exactly these sections:

# Enterprise Project Investigation Report

## Investigation Request

## Executive Summary

## Key Findings

## Risks

## Evidence Gaps

## Confidence

The report should be useful to an engineering manager or project
stakeholder.

Keep it concise but specific.
"""

        report = self.llm.generate(prompt)

        return {
            "report": report,
            "status": "report_generated",
        }