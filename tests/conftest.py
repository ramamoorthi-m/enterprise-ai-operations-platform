import pytest

from app.llm.client import GeminiClient


@pytest.fixture(autouse=True)
def block_real_gemini_calls(monkeypatch):
    """
    Prevent pytest from making real Gemini API calls.

    Individual tests that need LLM behavior must explicitly
    monkeypatch the appropriate GeminiClient method.
    """

    def blocked_generate(*args, **kwargs):
        raise RuntimeError(
            "Real Gemini API call blocked during pytest. "
            "Mock GeminiClient.generate() in this test."
        )

    def blocked_generate_structured(*args, **kwargs):
        raise RuntimeError(
            "Real Gemini API call blocked during pytest. "
            "Mock GeminiClient.generate_structured() in this test."
        )

    def blocked_generate_with_tools(*args, **kwargs):
        raise RuntimeError(
            "Real Gemini API call blocked during pytest. "
            "Mock GeminiClient.generate_with_tools() in this test."
        )

    monkeypatch.setattr(
        GeminiClient,
        "generate",
        blocked_generate,
    )

    monkeypatch.setattr(
        GeminiClient,
        "generate_structured",
        blocked_generate_structured,
    )

    monkeypatch.setattr(
        GeminiClient,
        "generate_with_tools",
        blocked_generate_with_tools,
    )