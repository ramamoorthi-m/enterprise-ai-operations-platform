import asyncio
import json

from app.workflow.graph import graph


async def main():
    """Run the complete workflow using the real Gemini API."""

    initial_state = {
        "user_query": (
            "Analyze the current project status and "
            "identify potential delivery blockers."
        ),

        "project": "SCRUM",

        "plan": [],

        "required_sources": [],

        "github_data": {},
        "jira_data": {},
        "doc_data": {},
        "slack_data": {},

        "findings": [],

        "report": "",

        "confidence": 0.0,

        "human_review_required": False,

        "errors": [],

        "status": "",

        "evaluation_passed": False,

        "retry_count": 0,
        "max_retries": 2,
    }

    print("=" * 70)
    print("REAL GEMINI ENTERPRISE AI INVESTIGATION")
    print("=" * 70)

    print("\nUser query:")
    print(initial_state["user_query"])

    print("\nStarting LangGraph workflow...")
    print("This run uses the REAL Gemini API.")
    print("Gemini API quota will be consumed.")

    result = await graph.ainvoke(initial_state)

    print("\n" + "=" * 70)
    print("WORKFLOW COMPLETED")
    print("=" * 70)

    print("\nStatus:")
    print(result.get("status"))

    print("\nEvaluation passed:")
    print(result.get("evaluation_passed"))

    print("\nConfidence:")
    print(result.get("confidence"))

    print("\nHuman review required:")
    print(result.get("human_review_required"))

    print("\nPlan:")
    print(json.dumps(
        result.get("plan", []),
        indent=2,
        default=str,
    ))

    print("\nInvestigation history:")
    print(json.dumps(
        result.get("investigation_history", []),
        indent=2,
        default=str,
    ))

    print("\nAnalysis:")
    print(json.dumps(
        result.get("analysis", {}),
        indent=2,
        default=str,
    ))

    print("\nFinal Report:")
    print("-" * 70)
    print(result.get("report", ""))
    print("-" * 70)

    if result.get("errors"):
        print("\nErrors:")
        print(json.dumps(
            result["errors"],
            indent=2,
            default=str,
        ))


if __name__ == "__main__":
    asyncio.run(main())