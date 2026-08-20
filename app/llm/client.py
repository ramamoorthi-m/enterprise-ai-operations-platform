import os
from typing import Type, TypeVar, Any, Callable

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()

T = TypeVar("T", bound=BaseModel)


class GeminiClient:
    """Centralized Gemini client for the application."""

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        if not model:
            raise ValueError(
                "GEMINI_MODEL is not configured."
            )

        self.model = model
        self.client = genai.Client(
            api_key=api_key
        )

    def generate(
        self,
        prompt: str,
    ) -> str:
        """Generate a text response from Gemini."""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        if not response.text:
            raise ValueError(
                "Gemini returned an empty response."
            )

        return response.text

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
    ) -> T:
        """Generate and validate a structured response from Gemini."""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": response_schema,
            },
        )

        if not response.text:
            raise ValueError(
                "Gemini returned an empty response."
            )

        return response_schema.model_validate_json(
            response.text
        )

    @staticmethod
    def _tool_to_function_declaration(
        tool: Any,
    ) -> types.FunctionDeclaration:
        """
        Convert a LangChain tool into a Gemini-safe
        FunctionDeclaration.

        Only serializable metadata is passed to Gemini.
        The actual LangChain/MCP tool object is never
        passed into GenerateContentConfig.
        """

        name = getattr(
            tool,
            "name",
            None,
        )

        if not name:
            raise ValueError(
                f"Tool has no name: {tool}"
            )

        description = getattr(
            tool,
            "description",
            "",
        )

        args_schema = getattr(
            tool,
            "args_schema",
            None,
        )

        if args_schema is not None:
            parameters_schema = (
                args_schema.model_json_schema()
            )
        else:
            parameters_schema = {
                "type": "object",
                "properties": {},
                "required": [],
            }

        return types.FunctionDeclaration(
            name=name,
            description=description,
            parameters_json_schema=parameters_schema,
        )

    @classmethod
    def _convert_tools(
        cls,
        tools: list[Any],
    ) -> list[types.Tool]:
        """
        Convert application tools into Gemini-safe
        function declarations.
        """

        function_declarations = []

        for tool in tools:
            declaration = (
                cls._tool_to_function_declaration(
                    tool
                )
            )

            function_declarations.append(
                declaration
            )

        return [
            types.Tool(
                function_declarations=function_declarations
            )
        ]

    def generate_with_tools(
        self,
        contents: Any,
        tools: list[Any],
        force_tool_call: bool = False,
    ):
        """
        Generate a Gemini response using manually
        declared function tools.

        Gemini receives only serializable function
        declarations. The actual tools remain in the
        InvestigationAgent and are executed there.
        """

        gemini_tools = self._convert_tools(
            tools
        )

        tool_config = None

        if force_tool_call:
            tool_config = types.ToolConfig(
                function_calling_config=(
                    types.FunctionCallingConfig(
                        mode="ANY",
                    )
                )
            )

        config = types.GenerateContentConfig(
            tools=gemini_tools,
            tool_config=tool_config,
            automatic_function_calling=(
                types.AutomaticFunctionCallingConfig(
                    disable=True
                )
            ),
        )

        return self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )