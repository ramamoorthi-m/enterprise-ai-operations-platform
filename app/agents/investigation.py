import inspect 
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

        self.tool_map = {}

        for tool in tools:
            name = getattr(tool, "name", None)

            if name is None:
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

        for iteration in range(
            1,
            self.max_iterations + 1,
        ):
            response = self.llm.generate_with_tools(
                contents=contents,
                tools=self.tools,
            )

            function_calls = response.function_calls

            # Gemini decided that no more tools are necessary.
            if not function_calls:
                return {
                    "status": "completed",
                    "investigation_complete": True,
                    "investigation_iteration": iteration,
                    "findings": (
                        [response.text]
                        if response.text
                        else []
                    ),
                    "investigation_history": history,
                }

            # Preserve Gemini's model response exactly.
            model_content = response.candidates[0].content

            contents.append(model_content)

            for function_call in function_calls:

                raw_tool_name = function_call.name
                arguments = function_call.args or {}
                tool_name = raw_tool_name.split(":")[-1].strip()

                tool = self.tool_map.get(tool_name)

                if tool is None:
                    raise ValueError(
                        f"Investigator requested unknown tool: "
                        f"{tool_name}"
                    )

                # Execute the LangChain tool.
                try:
                    if hasattr(tool, "ainvoke"):
                        result = await tool.ainvoke(arguments)

                    else:
                        result = tool(**arguments)

                        if inspect.isawaitable(result):
                            result = await result

                    

                except Exception as exc:
                    result={
                        "tool": tool_name,
                        "error": str(exc),
                        
                    }

                history.append(
                    {
                        "iteration": iteration,
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": result,
                    }
                )

                # Correct Gemini function-response format.
                function_response_part = (
                    types.Part.from_function_response(
                        name=tool_name,
                        response={
                            "result": result,
                        },
                    )
                )

                function_response_content = types.Content(
                    role="tool",
                    parts=[function_response_part],
                )

                contents.append(
                    function_response_content
                )

        return {
            "status": "max_iterations_reached",
            "investigation_complete": False,
            "investigation_iteration": self.max_iterations,
            "findings": [],
            "investigation_history": history,
        }

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
8. Stop when sufficient evidence has been collected.
9. Do not produce the final user report.

User query:
{state.get("user_query", "")}

Investigation plan:
{plan}

Current state:
{state}

Only use the tools provided to you.
"""