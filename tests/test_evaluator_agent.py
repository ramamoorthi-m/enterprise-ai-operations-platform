from app.agents.evaluator import EvaluatorAgent


class FakeLLM:

    def generate_structured(self, prompt, response_schema):

        return {
            "evaluation_passed": True,
            "confidence": 0.9,
            "reason": "The analysis is supported by the collected evidence.",
            "evidence_sufficient": True,
            "retry_required": False,
            "human_review_required": False,
        }
        


def test_evaluator_agent():

    state = {
        "analysis": {
            "summary": (
                "The project shows active development."
            ),
            "key_findings": [
                "Jira has no overdue tasks.",
                "GitHub shows recent development activity."
            ],
            "risks": [
                "Deployment status is unavailable."
            ],
            "evidence_gaps": [
                "No deployment information was retrieved."
            ],
            "confidence": 0.7
        },

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
                    "overdue_tasks": 0
                }
            }
        ]
    }

    agent = EvaluatorAgent(
        llm=FakeLLM()
    )

    result = agent.evaluate(state)

    print("\nEvaluator result:")
    print(result)

    assert result["evaluation_passed"] is True
    assert result["evidence_sufficient"] is True
    assert result["retry_required"] is False
    assert result["human_review_required"] is False
    assert 0 <= result["confidence"] <= 1