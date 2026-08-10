import os
from typing import Type, TypeVar

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel

load_dotenv()

T = TypeVar("T", bound=BaseModel)


class GeminiClient:
    """Centralized Gemini client for the application."""

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL")

        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        if not model:
            raise ValueError("GEMINI_MODEL is not configured.")

        self.model = model
        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt: str) -> str:
        """Generate a text response from Gemini."""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        if not response.text:
            raise ValueError("Gemini returned an empty response.")

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
            raise ValueError("Gemini returned an empty response.")

        return response_schema.model_validate_json(response.text)