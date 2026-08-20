import inspect
import os
from typing import Any, Callable

from google.genai import types

from app.llm.client import GeminiClient


class InvestigationAgent:
    """LLM-powered agent that executes an investigation plan."""

    def __init__(
        self,
        llm: GeminiClient,
        tools: list[Callable[..., Any]],
        max_iterations: int = 5,
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.max_iterations = max_iterations

        self.tool_map: dict[str, Callable[..., Any]] = {}

        for tool in tools:
            name = getattr(tool, "name", None)

            if name is None:
                raise ValueError(
                    f"Tool has no usable name: {tool}"
                )

            self.tool_map[name] = tool

    async def investigate(
        self,
        plan: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> dict[str, Any]:
        """Run the investigation loop."""

        contents: list[Any] = [
            self._build_prompt(plan, state)
        ]

        history: list[dict[str, Any]] = []

        required_sources = set(
            state.get("required_sources", [])
        )

        # ---------------------------------------------------------
        # Fallback: derive required sources from plan.
        # ---------------------------------------------------------

        if not required_sources:
            required_sources = {
                task.get("source")
                for task in plan
                if task.get("source")
            }

        for iteration in range(
            1,
            self.max_iterations + 1,
        ):
            # -----------------------------------------------------
            # Ask Gemini what to do next.
            # -----------------------------------------------------

            response = self.llm.generate_with_tools(
                contents=contents,
                tools=self.tools,
                force_tool_call=(
                    iteration == 1 and not history
                ),
            )

            function_calls = response.function_calls

            # =====================================================
            # GEMINI DID NOT REQUEST A TOOL
            # =====================================================

            if not function_calls:

                executed_sources = (
                    self._get_executed_sources(history)
                )

                missing_sources = (
                    required_sources - executed_sources
                )

                # -------------------------------------------------
                # Tool failure handling
                #
                # A tool was actually executed but failed.
                # Gemini has now decided to stop the investigation.
                #
                # Preserve the failure in investigation_history.
                # The Evaluator is responsible for deciding whether
                # the evidence is sufficient and whether retry is
                # required.
                # -------------------------------------------------

                tool_errors = [
                    item
                    for item in history
                    if isinstance(item.get("result"), dict)
                    and item["result"].get("error")
                ]

                if tool_errors and response.text:
                    return {
                        "status": (
                            "investigation_completed_with_errors"
                        ),
                        "investigation_complete": True,
                        "investigation_iteration": iteration,
                        "findings": [response.text],
                        "investigation_history": history,
                    }

                # -------------------------------------------------
                # Deterministic fallback.
                #
                # If Gemini fails to request a tool, follow the
                # planner's instructions ourselves.
                #
                # This prevents the investigation from ending with
                # zero evidence merely because the LLM stopped
                # making tool calls.
                # -------------------------------------------------

                next_tool, next_arguments = (
                    self._get_next_planned_tool(
                        plan=plan,
                        history=history,
                        state=state,
                    )
                )

                if next_tool:
                    result = await self._execute_tool(
                        tool_name=next_tool,
                        arguments=next_arguments,
                    )

                    history.append(
                        {
                            "iteration": iteration,
                            "tool": next_tool,
                            "arguments": next_arguments,
                            "result": result,
                        }
                    )

                    contents.append(
                        self._build_function_response(
                            tool_name=next_tool,
                            result=result,
                        )
                    )

                    continue

                # -------------------------------------------------
                # No planned tool remains.
                # -------------------------------------------------

                if not history:

                    if iteration >= self.max_iterations:
                        return {
                            "status": "max_iterations_reached",
                            "investigation_complete": False,
                            "investigation_iteration": iteration,
                            "findings": [],
                            "investigation_history": history,
                        }

                    contents.append(
                        """
You have not executed any investigation tools yet.

You MUST collect factual evidence before completing
the investigation.

Review the investigation plan and call the appropriate
available Jira or GitHub tools.

Do not provide a conclusion yet.
"""
                    )

                    continue

                # -------------------------------------------------
                # Required source is still missing.
                # -------------------------------------------------

                if missing_sources:

                    if iteration >= self.max_iterations:
                        return {
                            "status": "max_iterations_reached",
                            "investigation_complete": False,
                            "investigation_iteration": iteration,
                            "findings": [],
                            "investigation_history": history,
                        }

                    missing_source_text = ", ".join(
                        sorted(missing_sources)
                    )

                    contents.append(
                        f"""
The investigation is not complete.

Required investigation sources that have NOT yet
been investigated:

{missing_source_text}

You must continue collecting evidence from the
missing source(s).

Do not claim that the investigation is complete
until the required sources have actually been
queried.

Do not invent evidence.
"""
                    )

                    continue

                # -------------------------------------------------
                # All planned sources/tools have been investigated.
                # -------------------------------------------------

                return {
                    "status": "investigation_completed",
                    "investigation_complete": True,
                    "investigation_iteration": iteration,
                    "findings": (
                        [response.text]
                        if response.text
                        else []
                    ),
                    "investigation_history": history,
                }

            # =====================================================
            # GEMINI REQUESTED TOOL(S)
            # =====================================================

            model_content = response.candidates[0].content

            contents.append(model_content)

            for function_call in function_calls:

                raw_tool_name = function_call.name

                arguments = (
                    function_call.args
                    or {}
                )

                tool_name = (
                    raw_tool_name
                    .split(":")[-1]
                    .strip()
                )

                tool = self.tool_map.get(tool_name)

                # -------------------------------------------------
                # Unknown tool requested by Gemini.
                # -------------------------------------------------

                if tool is None:

                    result = {
                        "tool": tool_name,
                        "error": (
                            f"Unknown tool requested: "
                            f"{tool_name}. "
                            f"Available tools: "
                            f"{list(self.tool_map.keys())}"
                        ),
                    }

                    history.append(
                        {
                            "iteration": iteration,
                            "tool": tool_name,
                            "arguments": arguments,
                            "result": result,
                        }
                    )

                    contents.append(
                        f"""
The requested tool '{tool_name}' does not exist.

Available tools:
{list(self.tool_map.keys())}

Do not request unavailable tools.

Choose one of the available tools that matches
the investigation plan.
"""
                    )

                    continue

                # -------------------------------------------------
                # Execute actual tool.
                # -------------------------------------------------

                result = await self._execute_tool(
                    tool_name=tool_name,
                    arguments=arguments,
                )

                # -------------------------------------------------
                # Store complete tool execution history.
                # -------------------------------------------------

                history.append(
                    {
                        "iteration": iteration,
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": result,
                    }
                )

                # -------------------------------------------------
                # Send tool result back to Gemini.
                # -------------------------------------------------

                contents.append(
                    self._build_function_response(
                        tool_name=tool_name,
                        result=result,
                    )
                )

        # =========================================================
        # MAXIMUM ITERATIONS REACHED
        # =========================================================

        return {
            "status": "max_iterations_reached",
            "investigation_complete": False,
            "investigation_iteration": self.max_iterations,
            "findings": [],
            "investigation_history": history,
        }

    # =================================================================
    # DETERMINISTIC PLANNED TOOL SELECTION
    # =================================================================

    def _get_next_planned_tool(
        self,
        plan: list[dict[str, Any]],
        history: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> tuple[str | None, dict[str, Any]]:

        executed_tools = {
            item.get("tool")
            for item in history
        }

        project = state.get(
            "project",
            "SCRUM",
        )

        repository = (
            state.get("github_repository")
            or os.getenv("GITHUB_REPOSITORY")
            or (
                f"{os.getenv('GITHUB_OWNER')}/"
                f"{os.getenv('GITHUB_REPO')}"
            )
        )

        for task in plan:

            description = (
                task.get("description", "")
                .lower()
            )

            source = task.get("source")

            # -----------------------------------------------------
            # Jira
            # -----------------------------------------------------

            if source == "jira":

                if (
                    "blocked" in description
                    and "jira_get_blocked_tasks"
                    not in executed_tools
                    and "jira_get_blocked_tasks"
                    in self.tool_map
                ):
                    return (
                        "jira_get_blocked_tasks",
                        {"project": project},
                    )

                if (
                    "overdue" in description
                    and "jira_get_overdue_tasks"
                    not in executed_tools
                    and "jira_get_overdue_tasks"
                    in self.tool_map
                ):
                    return (
                        "jira_get_overdue_tasks",
                        {"project": project},
                    )

                if (
                    "open" in description
                    and "jira_get_open_tasks"
                    not in executed_tools
                    and "jira_get_open_tasks"
                    in self.tool_map
                ):
                    return (
                        "jira_get_open_tasks",
                        {"project": project},
                    )

                if (
                    "sprint" in description
                    and "jira_get_current_sprint"
                    not in executed_tools
                    and "jira_get_current_sprint"
                    in self.tool_map
                ):
                    return (
                        "jira_get_current_sprint",
                        {"project": project},
                    )

            # -----------------------------------------------------
            # GitHub
            # -----------------------------------------------------

            elif source == "github":

                if (
                    "deployment" in description
                    and "github_get_deployment_status"
                    not in executed_tools
                    and "github_get_deployment_status"
                    in self.tool_map
                ):
                    return (
                        "github_get_deployment_status",
                        {"repository": repository},
                    )

                if (
                    "commit" in description
                    and "github_get_recent_commits"
                    not in executed_tools
                    and "github_get_recent_commits"
                    in self.tool_map
                ):
                    return (
                        "github_get_recent_commits",
                        {"repository": repository},
                    )

                if (
                    "issue" in description
                    and "github_get_repository_issues"
                    not in executed_tools
                    and "github_get_repository_issues"
                    in self.tool_map
                ):
                    return (
                        "github_get_repository_issues",
                        {"repository": repository},
                    )

        return None, {}

    # =================================================================
    # TOOL EXECUTION
    # =================================================================

    async def _execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:

        tool = self.tool_map.get(tool_name)

        if tool is None:
            return {
                "tool": tool_name,
                "error": (
                    f"Unknown tool requested: "
                    f"{tool_name}. "
                    f"Available tools: "
                    f"{list(self.tool_map.keys())}"
                ),
            }

        try:

            if hasattr(tool, "ainvoke"):

                result = await tool.ainvoke(
                    arguments
                )

            else:

                result = tool(
                    **arguments
                )

                if inspect.isawaitable(result):
                    result = await result

            return result

        except Exception as exc:

            # Tool failures are recorded as evidence rather
            # than crashing the entire investigation.
            return {
                "tool": tool_name,
                "error": str(exc),
            }

    # =================================================================
    # GEMINI FUNCTION RESPONSE
    # =================================================================

    @staticmethod
    def _build_function_response(
        tool_name: str,
        result: Any,
    ) -> types.Content:

        function_response_part = (
            types.Part.from_function_response(
                name=tool_name,
                response={
                    "result": result,
                },
            )
        )

        return types.Content(
            role="tool",
            parts=[
                function_response_part
            ],
        )

    # =================================================================
    # SOURCE TRACKING
    # =================================================================

    @staticmethod
    def _get_executed_sources(
        history: list[dict[str, Any]],
    ) -> set[str]:

        executed_sources: set[str] = set()

        for item in history:

            tool_name = item.get(
                "tool",
                "",
            )

            if tool_name.startswith("jira_"):
                executed_sources.add("jira")

            elif tool_name.startswith("github_"):
                executed_sources.add("github")

        return executed_sources

    # =================================================================
    # INITIAL INVESTIGATION PROMPT
    # =================================================================

    def _build_prompt(
        self,
        plan: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> str:

        return f"""
You are the Investigation Agent for an enterprise AI operations platform.

Your job is to investigate the user's goal using the investigation plan
created by the Planner Agent.

You are NOT the Planner.
Do not create a new investigation plan.

Your responsibilities:

1. Follow the investigation plan.
2. Decide which available tool should be used next.
3. Use tools to collect factual evidence.
4. Observe the returned evidence.
5. Decide whether additional investigation is necessary.
6. Avoid unnecessary or duplicate tool calls.
7. Do not invent information.
8. Do not claim that a source was investigated unless you actually
   executed a tool from that source.
9. Do not claim that evidence was collected when no tool result exists.
10. Stop only after the required investigation sources have actually
    been investigated.
11. Do not produce the final user report.

User query:
{state.get("user_query", "")}

Project:
{state.get("project", "")}

GitHub repository:
{state.get("github_repository", "")}

Investigation plan:
{plan}

Required sources:
{state.get("required_sources", [])}

Current state:
{state}

AVAILABLE TOOL NAMES:

Jira:
- jira_get_open_tasks
- jira_get_blocked_tasks
- jira_get_overdue_tasks
- jira_get_current_sprint

GitHub:
- github_get_repository_issues
- github_get_recent_commits
- github_get_deployment_status

STRICT TOOL RULES:

- You may ONLY call tools whose exact names appear above.
- Never invent a tool name.
- Never modify a tool name.
- Never add prefixes such as "test_", "mock_", or "fake_".
- If the required information cannot be obtained using these tools,
  do not invent another tool.
- Use the available tools that best match the investigation plan.
- Evidence must come from actual tool results.
- Do not stop merely because you have partial evidence.
"""