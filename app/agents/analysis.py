from typing import Any

from app.llm.groq_client import GroqClient
from app.state.analysis import AnalysisResult


class AnalysisAgent:
    """LLM-powered agent that analyzes collected enterprise evidence."""

    def __init__(self, llm: GroqClient) -> None:
        self.llm = llm

    def analyze(
        self,
        state: dict[str, Any],
    ) -> AnalysisResult:
        """Analyze collected evidence and produce a structured assessment."""

        prompt = self._build_prompt(state)

        return self.llm.generate_structured(
            prompt=prompt,
            response_schema=AnalysisResult,
        )

    def _build_prompt(
        self,
        state: dict[str, Any],
    ) -> str:

        return f"""
You are the Analysis Agent for an enterprise AI operations platform.

Your responsibility is to analyze evidence collected by the
Investigation Agent.

You are NOT the Planner.
You are NOT the Investigation Agent.
You are NOT the Evaluator.
You are NOT the Report Generator.

Do not perform new investigation.
Do not call tools.
Do not invent missing information.

Your job is to determine what the collected evidence means.

USER QUERY:
{state.get("user_query", "")}

PROJECT:
{state.get("project", "")}

INVESTIGATION PLAN:
{state.get("plan", [])}

REQUIRED SOURCES:
{state.get("required_sources", [])}

GITHUB EVIDENCE:
{state.get("github_data", {})}

JIRA EVIDENCE:
{state.get("jira_data", {})}

DOCUMENT EVIDENCE:
{state.get("doc_data", {})}

SLACK EVIDENCE:
{state.get("slack_data", {})}

INVESTIGATION HISTORY:
{state.get("investigation_history", [])}

CURRENT FINDINGS:
{state.get("findings", [])}

ANALYSIS RULES:

1. Base every conclusion on the supplied evidence.
2. Do not invent facts.
3. Distinguish facts from interpretations.
4. Identify meaningful relationships between evidence from
   different enterprise systems.
5. Identify potential delivery risks.
6. Identify important evidence gaps.
7. If evidence is insufficient, explicitly say so.
8. Do not treat missing evidence as proof of a problem.
9. Assign confidence between 0.0 and 1.0 based on evidence quality.
10. Keep the assessment concise and evidence-grounded.
11. Do not generate the final operational report.

Return only the structured AnalysisResult.
"""