import json
from pydantic import BaseModel, Field

from app.llm.client import GeminiClient

class EvaluatorResult(BaseModel):
    evaluation_passed: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    evidence_sufficient: bool
    retry_required: bool
    human_review_required: bool


class EvaluatorAgent:

    def __init__(self, llm: GeminiClient):
        self.llm = llm

    def evaluate(self, state):
        analysis = state.get("analysis", {})
        findings = state.get("findings", [])
        investigation_history = state.get(
            "investigation_history",
            []
        )

        prompt = f"""
You are an enterprise AI workflow evaluator.

Evaluate whether the investigation produced enough reliable
evidence to generate a final project-status report.

You must evaluate:

1. Whether the analysis is supported by the evidence.
2. Whether important evidence gaps remain.
3. Whether the confidence is sufficient.
4. Whether another investigation attempt could reasonably
   resolve the missing evidence.
5. Whether human review is required.

Analysis:
{json.dumps(analysis, indent=2)}

Findings:
{json.dumps(findings, indent=2)}

Investigation history:
{json.dumps(investigation_history, indent=2)}

Return ONLY valid JSON.

Use exactly this structure:

{{
    "evaluation_passed": true,
    "confidence": 0.0,
    "reason": "Short explanation",
    "evidence_sufficient": true,
    "retry_required": false,
    "human_review_required": false
}}

Rules:

- evaluation_passed = true only when the evidence is sufficient
  for a useful final report.
- retry_required = true when additional investigation could
  reasonably collect the missing evidence.
- human_review_required = true when human judgment is required
  or the evidence remains unreliable.
- confidence must be a number between 0 and 1.
"""

        response = self.llm.generate_structured(prompt, EvaluatorResult)

        result = self._parse_response(response)

        return result

    @staticmethod
    def _parse_response(response):

        if isinstance(response, BaseModel):
            result = response.model_dump()
        
        elif isinstance(response, dict):
            result = response


        else:
            response = response.strip()

            # Handle Markdown JSON fences
            if response.startswith("json"):
                response = response[len("json"):].strip()

            elif response.startswith(""):
                response = response[len(""):].strip()

            if response.endswith("```"):
                response = response[:-3].strip()

            try:
                result = json.loads(response)

            except json.JSONDecodeError as exc:
                raise ValueError(
                    "Evaluator returned invalid JSON"
                ) from exc

        # Ensure the parsed response is a dictionary
        if not isinstance(result, dict):
            raise ValueError(
                "Evaluator response must be a JSON object"
            )

        required_fields = {
            "evaluation_passed",
            "confidence",
            "reason",
            "evidence_sufficient",
            "retry_required",
            "human_review_required",
        }

        missing_fields = required_fields - result.keys()

        if missing_fields:
            raise ValueError(
                f"Evaluator response missing fields: "
                f"{sorted(missing_fields)}"
            )

        confidence = result["confidence"]

        if not isinstance(confidence, (int, float)):
            raise ValueError(
                "Evaluator confidence must be numeric"
            )

        if not 0 <= confidence <= 1:
            raise ValueError(
                "Evaluator confidence must be between 0 and 1"
            )

        return result