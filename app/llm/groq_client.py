import json
import os
from typing import Type, TypeVar, Any

from dotenv import load_dotenv
from groq import Groq, BadRequestError
from pydantic import BaseModel


load_dotenv()


T = TypeVar("T", bound=BaseModel)


class GroqClient:
    """Client for Groq-hosted LLMs."""

    def __init__(
        self,
        model: str = "openai/gpt-oss-120b",
    ) -> None:

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY environment variable is not set."
            )

        self.model = model

        self.client = Groq(
            api_key=api_key
        )

    def generate(
        self,
        prompt: str,
    ) -> str:
        """Generate a normal text response."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return (
            response.choices[0]
            .message
            .content
            or ""
        )

    @staticmethod
    def _make_groq_schema(
        response_schema: Type[BaseModel],
    ) -> dict[str, Any]:
        """
        Convert a Pydantic JSON schema into a schema
        compatible with Groq strict structured outputs.
        """

        schema = response_schema.model_json_schema()

        def enforce_strict_objects(node: Any) -> None:

            if isinstance(node, dict):

                if node.get("type") == "object":
                    node["additionalProperties"] = False

                    properties = node.get(
                        "properties",
                        {},
                    )

                    if properties:
                        node["required"] = list(
                            properties.keys()
                        )

                for value in node.values():
                    enforce_strict_objects(value)

            elif isinstance(node, list):

                for item in node:
                    enforce_strict_objects(item)

        enforce_strict_objects(schema)

        return schema

    @staticmethod
    def _build_structured_retry_prompt(
        prompt: str,
    ) -> str:
        """
        Add explicit instructions for the retry attempt.

        This is used only when Groq fails to produce valid
        structured JSON.
        """

        return f"""
{prompt}

CRITICAL STRUCTURED OUTPUT REQUIREMENTS:

Return ONLY a valid JSON object matching the requested schema.

Do not use Markdown.
Do not use code fences.
Do not write explanations outside the JSON object.

Every numeric field MUST contain a real JSON number.

For example:
- Correct: 0.85
- Correct: 1
- Incorrect: "0.85"
- Incorrect: 0. Eighty Five
- Incorrect: 0. Nine
- Incorrect: eighty five percent

Boolean fields MUST be JSON booleans:
- true
- false

String fields MUST contain strings.

Make absolutely sure the final response can be parsed
directly by a strict JSON parser.
"""

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
    ) -> T:
        """
        Generate a response conforming to a Pydantic schema.

        Groq strict structured output is used first.

        If Groq rejects its own generated JSON because of a
        structured-output formatting error, retry once with
        stricter JSON instructions.
        """

        schema = self._make_groq_schema(
            response_schema
        )

        def generate_once(
            request_prompt: str,
        ):
            return self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": request_prompt,
                    }
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": response_schema.__name__,
                        "strict": True,
                        "schema": schema,
                    },
                },
            )

        # ---------------------------------------------------------
        # First attempt
        # ---------------------------------------------------------

        try:

            response = generate_once(prompt)

        except BadRequestError as exc:

            error_text = str(exc)

            # -----------------------------------------------------
            # Groq rejected its generated JSON.
            #
            # Retry once with stricter formatting instructions.
            # -----------------------------------------------------

            if "json_validate_failed" not in error_text:
                raise

            retry_prompt = (
                self._build_structured_retry_prompt(
                    prompt
                )
            )

            try:

                response = generate_once(
                    retry_prompt
                )

            except BadRequestError:
                # Do not hide the second failure.
                raise

        content = (
            response.choices[0]
            .message
            .content
        )

        if not content:
            raise RuntimeError(
                "Groq returned an empty response."
            )

        try:

            data = json.loads(content)

        except json.JSONDecodeError as exc:

            raise RuntimeError(
                "Groq returned invalid JSON."
            ) from exc

        try:

            return response_schema.model_validate(
                data
            )

        except Exception as exc:

            raise RuntimeError(
                "Groq returned JSON that does not "
                "match the requested schema."
            ) from exc