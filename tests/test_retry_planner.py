from app.llm.client import GeminiClient
from app.state.plan import InvestigationPlan
from app.workflow.planner import planner


def test_llm_planner(monkeypatch):

    fake_plan = InvestigationPlan(
        project="Project Alpha",
        goal="Analyze the current project status and identify potential delivery blockers.",
        tasks=[
            {
                "description": "Find overdue Jira issues and blocked tasks",
                "source": "jira",
            },
            {
                "description": "Inspect recent GitHub commits and pull requests",
                "source": "github",
            },
        ],
        required_sources=["jira", "github"],
    )

    def fake_generate_structured(self, prompt, response_schema):
        return fake_plan

    monkeypatch.setattr(
        GeminiClient,
        "generate_structured",
        fake_generate_structured,
    )

    llm = GeminiClient()

    query = (
        "Analyze the current project status "
        "and identify potential delivery blockers."
    )

    prompt = f"""
You are an enterprise investigation planning agent.

Analyze the user's request and create an investigation plan.

Available sources:
- GitHub: repositories, pull requests, commits, issues
- Jira: projects, tickets, sprint status, blockers

Rules:
- Only use github or jira.
- Do not invent information.
- Create concrete investigation tasks.
- Every task must specify a source.
- Focus on evidence collection.

User request:
{query}
"""

    plan = llm.generate_structured(
        prompt=prompt,
        response_schema=InvestigationPlan,
    )

    print("\nGenerated plan:")
    print(plan.model_dump_json(indent=2))

    assert plan.goal
    assert plan.project == "Project Alpha"
    assert plan.tasks
    assert plan.required_sources

    for task in plan.tasks:
        assert task.source in {"github", "jira"}


def test_planner_uses_previous_context_on_retry(monkeypatch):
    """
    Verify that the planner uses evidence from the previous
    investigation attempt when creating a retry plan.
    """

    captured_prompt = {}

    fake_plan = InvestigationPlan(
        project="SCRUM",
        goal="Collect missing deployment evidence.",
        tasks=[
            {
                "description": "Inspect GitHub deployment status",
                "source": "github",
            }
        ],
        required_sources=["github"],
    )

    def fake_generate_structured(
        self,
        prompt,
        response_schema,
    ):
        captured_prompt["value"] = prompt
        return fake_plan

    monkeypatch.setattr(
        GeminiClient,
        "generate_structured",
        fake_generate_structured,
    )

    state = {
        "user_query": (
            "Analyze the current project status "
            "and identify potential delivery blockers."
        ),

        # Retry attempt.
        "retry_count": 1,

        # Previous investigation plan.
        "plan": [
            {
                "description": "Find overdue Jira issues",
                "source": "jira",
            },
            {
                "description": "Inspect recent GitHub commits",
                "source": "github",
            },
        ],

        # Evidence collected during the first attempt.
        "findings": [
            "Jira shows no overdue tasks.",
            "GitHub shows recent development activity.",
        ],

        # Analysis from the first attempt.
        "analysis": {
            "summary": (
                "The investigation did not collect "
                "deployment evidence."
            ),
            "evidence_gaps": [
                "No deployment information was retrieved."
            ],
        },

        "errors": [],
    }

    result = planner(state)

    prompt = captured_prompt["value"]

    print("\nRetry planner prompt:")
    print(prompt)

    print("\nRetry planner result:")
    print(result)

    # ----------------------------------------------------------
    # Verify retry context was passed to the LLM
    # ----------------------------------------------------------

    assert "retry attempt 2" in prompt

    assert (
        "No deployment information was retrieved."
        in prompt
    )

    assert (
        "The investigation did not collect deployment evidence."
        in prompt
    )

    assert (
        "Do NOT blindly repeat the previous investigation."
        in prompt
    )

    # ----------------------------------------------------------
    # Verify planner still returned a valid plan
    # ----------------------------------------------------------

    assert result["status"] == "planning_completed"
    assert result["project"] == "SCRUM"
    assert result["plan"]

    assert result["required_sources"] == ["github"]