import os

from app.llm.client import GeminiClient


def test_gemini_client_does_not_retry_429(monkeypatch):
    captured = {}

    class FakeGenAIClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setattr(
        "app.llm.client.genai.Client",
        FakeGenAIClient,
    )

    GeminiClient()

    retry_options = captured["http_options"].retry_options

    assert 429 not in retry_options.http_status_codes
    assert 500 in retry_options.http_status_codes
    assert 502 in retry_options.http_status_codes
    assert 503 in retry_options.http_status_codes
    assert 504 in retry_options.http_status_codes