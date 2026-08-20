from pydantic import BaseModel, Field

from app.llm.groq_client import GroqClient


class ProjectAssessment(BaseModel):
    summary: str
    risk_level: str
    confidence: float = Field(ge=0.0, le=1.0)


def main():

    client = GroqClient()

    result = client.generate_structured(
        prompt="""
Analyze this project situation:

There is one overdue Jira task.
The GitHub repository has recent development activity.
No deployment failure has been reported.

Return a concise project assessment.
""",
        response_schema=ProjectAssessment,
    )

    print("\nStructured Groq response:")
    print(result)


if __name__ == "__main__":
    main()