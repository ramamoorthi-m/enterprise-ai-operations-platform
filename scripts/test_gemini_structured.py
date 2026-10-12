from app.llm.client import GeminiClient
from app.state.plan import InvestigationPlan

client = GeminiClient()

prompt = """
Create an investigation plan for the project SCRUM.
The goal is to summarize current operations.

Use these fields:
- project: SCRUM
- goal: summarize current operations
- tasks: one Jira task to retrieve open tasks
- required_sources: jira

Return the result using the supplied schema.
"""

try:
    print("Testing Gemini structured generation...")
    result = client.generate_structured(
        prompt=prompt,
        response_schema=InvestigationPlan,
    )
    print("SUCCESS")
    print(result.model_dump_json(indent=2))

except Exception as exc:
    print("FAILED")
    print(f"{type(exc).__name__}: {exc}")

finally:
    client.client.close()