import json

from pydantic import BaseModel, Field

from app.llm.groq_client import GroqClient


class EvaluatorResult(BaseModel):
    evaluation_passed: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    evidence_sufficient: bool
    retry_required: bool
    human_review_required: bool


class EvaluatorAgent:
    """Evaluate whether the investigation produced sufficient evidence."""

    def __init__(self, llm: GroqClient):
        self.llm = llm

    def evaluate(self, state):
        analysis = state.get("analysis", {})
        findings = state.get("findings", [])

        investigation_history = state.get(
            "investigation_history",
            [],
        )

        plan = state.get(
            "plan",
            [],
        )

        required_sources = state.get(
            "required_sources",
            [],
        )

        github_data = state.get(
            "github_data",
            {},
        )

        jira_data = state.get(
            "jira_data",
            {},
        )

        prompt = f"""
You are the Evaluation Agent in an enterprise AI operations platform.

Your responsibility is to determine whether the investigation collected
enough reliable evidence to produce a useful final project-status report.

You are NOT the investigator.
You are NOT the report generator.

Evaluate the evidence objectively.

============================================================
USER REQUEST
============================================================

{state.get("user_query", "")}

============================================================
INVESTIGATION PLAN
============================================================

{json.dumps(plan, indent=2, default=str)}

============================================================
REQUIRED SOURCES
============================================================

{json.dumps(required_sources, indent=2, default=str)}

============================================================
COLLECTED JIRA EVIDENCE
============================================================

{json.dumps(jira_data, indent=2, default=str)}

============================================================
COLLECTED GITHUB EVIDENCE
============================================================

{json.dumps(github_data, indent=2, default=str)}

============================================================
ANALYSIS
============================================================

{json.dumps(analysis, indent=2, default=str)}

============================================================
FINDINGS
============================================================

{json.dumps(findings, indent=2, default=str)}

============================================================
INVESTIGATION HISTORY
============================================================

{json.dumps(investigation_history, indent=2, default=str)}

============================================================
EVALUATION RULES
============================================================

1. Check whether the important objectives in the investigation plan
   were actually investigated.

2. Use investigation_history as the authoritative record of which
   tools were actually executed.

3. Do NOT assume that a source was investigated simply because:
   - it appears in the plan,
   - it appears in required_sources,
   - the Investigator claims it was investigated,
   - or another source contains evidence.

4. Evidence must come from actual tool execution results.

5. Determine whether the collected evidence supports the analysis.

6. Identify important evidence gaps.

7. If important evidence is missing AND another investigation attempt
   could reasonably obtain that evidence:
      evidence_sufficient = false
      retry_required = true

8. If the available evidence is sufficient for a useful report:
      evidence_sufficient = true
      evaluation_passed = true
      retry_required = false

9. Do not require every possible enterprise data source.
   Evaluate against the actual investigation plan and required sources.

10. A useful report may still contain evidence gaps.
    Evidence gaps alone do not automatically mean evaluation failure.

11. If the investigation has enough evidence to make a reasonable
    assessment but some uncertainty remains, evaluation may pass with
    an appropriately reduced confidence.

12. Set human_review_required = true when:
    - evidence is contradictory,
    - evidence is unreliable,
    - confidence is very low,
    - or the decision requires human judgment.

13. Do not mark human review as required merely because some optional
    information is unavailable.

14. Confidence must represent confidence in the overall assessment,
    not confidence that every possible data source was checked.

15. Do not invent evidence.

============================================================
DECISION GUIDANCE
============================================================

For example:

If the plan requires Jira and GitHub and the investigation history
contains successful Jira and GitHub tool calls with meaningful results,
the investigation may be sufficient even if Slack and documents were
not queried.

If the plan requires GitHub deployment status but only GitHub commits
were collected, the deployment objective remains incomplete.

If a tool was executed but returned an error or empty result, treat
that evidence as unavailable unless the result itself is meaningful
evidence that the requested resource has no matching records.

If another investigation attempt could obtain missing required
evidence, retry_required should be true.

============================================================
OUTPUT
============================================================

Return ONLY a valid JSON object.

Use exactly this structure:

{{
    "evaluation_passed": true,
    "confidence": 0.0,
    "reason": "Short explanation of the evaluation decision.",
    "evidence_sufficient": true,
    "retry_required": false,
    "human_review_required": false
}}
"""

        response = self.llm.generate_structured(
            prompt=prompt,
            response_schema=EvaluatorResult,
        )

        return self._parse_response(response)

    @staticmethod
    def _parse_response(response):
        """
        Normalize and validate the structured evaluator response.
        """

        if isinstance(response, BaseModel):
            result = response.model_dump()

        elif isinstance(response, dict):
            result = response

        elif isinstance(response, str):
            text = response.strip()

            # Remove optional markdown JSON fences.
            if text.startswith("```json"):
                text = text[len("```json"):].strip()

            elif text.startswith("```"):
                text = text[len("```"):].strip()

            if text.endswith("```"):
                text = text[:-3].strip()

            try:
                result = json.loads(text)

            except json.JSONDecodeError as exc:
                raise ValueError(
                    "Evaluator returned invalid JSON."
                ) from exc

        else:
            raise TypeError(
                "Unsupported evaluator response type."
            )

        if not isinstance(result, dict):
            raise ValueError(
                "Evaluator response must be a JSON object."
            )

        required_fields = {
            "evaluation_passed",
            "confidence",
            "reason",
            "evidence_sufficient",
            "retry_required",
            "human_review_required",
        }

        missing_fields = (
            required_fields - result.keys()
        )

        if missing_fields:
            raise ValueError(
                "Evaluator response missing fields: "
                f"{sorted(missing_fields)}"
            )

        confidence = result["confidence"]

        if not isinstance(
            confidence,
            (int, float),
        ):
            raise ValueError(
                "Evaluator confidence must be numeric."
            )

        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                "Evaluator confidence must be between 0 and 1."
            )

        return result