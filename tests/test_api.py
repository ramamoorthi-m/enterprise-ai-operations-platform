from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from langgraph.types import Command

from app.api.main import app


client = TestClient(app)


def make_result(**overrides):
    result = {
        "status": "report_generated",
        "evaluation_passed": True,
        "confidence": 0.9,
        "human_review_required": False,
        "human_review_reason": "",
        "plan": [{"description": "Check deployment", "source": "github"}],
        "investigation_history": [],
        "analysis": {"summary": "Deployment completed"},
        "report": "Investigation completed successfully.",
        "errors": [],
    }
    result.update(overrides)
    return result


def test_health_returns_200():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@patch("app.api.main.graph.ainvoke", new_callable=AsyncMock)
def test_investigate_returns_report(mock_ainvoke):
    mock_ainvoke.return_value = make_result()

    response = client.post(
        "/api/v1/investigate",
        json={"query": "Why is the deployment delayed?"},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "report_generated"
    assert body["evaluation_passed"] is True
    assert body["thread_id"]
    assert body["final_report"] == "Investigation completed successfully."
    mock_ainvoke.assert_awaited_once()


@patch("app.api.main.graph.ainvoke", new_callable=AsyncMock)
def test_investigate_returns_human_review_pause(mock_ainvoke):
    review = {
        "type": "human_review",
        "reason": "The evidence is insufficient.",
        "confidence": 0.45,
        "findings": ["Deployment status is unclear."],
        "analysis": {"summary": "Needs manual verification"},
    }

    # LangGraph returns interrupt objects in __interrupt__.
    class FakeInterrupt:
        value = review

    mock_ainvoke.return_value = make_result(
        status="evaluating",
        human_review_required=True,
        __interrupt__=(FakeInterrupt(),),
    )

    response = client.post(
        "/api/v1/investigate",
        json={"query": "Why is the deployment delayed?"},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "awaiting_human_review"
    assert body["human_review_required"] is True
    assert body["human_review_reason"] == review["reason"]
    assert body["review_payload"] == review


@patch("app.api.main.graph.ainvoke", new_callable=AsyncMock)
@patch("app.api.main.graph.aget_state", new_callable=AsyncMock)
def test_resume_approved_investigation(mock_get_state, mock_ainvoke):
    class FakeTask:
        interrupts = [object()]

    class FakeSnapshot:
        tasks = [FakeTask()]

    mock_get_state.return_value = FakeSnapshot()
    mock_ainvoke.return_value = make_result()

    response = client.post(
        "/api/v1/investigate/resume",
        json={
            "thread_id": "test-thread-123",
            "decision": "approve",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "report_generated"

    mock_get_state.assert_awaited_once()
    mock_ainvoke.assert_awaited_once()

    command = mock_ainvoke.await_args.args[0]
    assert isinstance(command, Command)
    assert command.resume == "approve"


@patch("app.api.main.graph.ainvoke", new_callable=AsyncMock)
@patch("app.api.main.graph.aget_state", new_callable=AsyncMock)
def test_resume_retry_decision(mock_get_state, mock_ainvoke):
    class FakeTask:
        interrupts = [object()]

    class FakeSnapshot:
        tasks = [FakeTask()]

    mock_get_state.return_value = FakeSnapshot()
    mock_ainvoke.return_value = make_result(
        status="report_generated",
        retry_count=1,
    )

    response = client.post(
        "/api/v1/investigate/resume",
        json={
            "thread_id": "test-thread-123",
            "decision": "retry",
        },
    )

    assert response.status_code == 200
    command = mock_ainvoke.await_args.args[0]
    assert isinstance(command, Command)
    assert command.resume == "retry"


@patch("app.api.main.graph.ainvoke", new_callable=AsyncMock)
@patch("app.api.main.graph.aget_state", new_callable=AsyncMock)
def test_resume_rejects_investigation_not_paused(
    mock_get_state,
    mock_ainvoke,
):
    class FakeSnapshot:
        tasks = []

    mock_get_state.return_value = FakeSnapshot()

    response = client.post(
        "/api/v1/investigate/resume",
        json={
            "thread_id": "test-thread-123",
            "decision": "approve",
        },
    )

    assert response.status_code == 409
    mock_ainvoke.assert_not_awaited()


def test_resume_rejects_invalid_decision():
    response = client.post(
        "/api/v1/investigate/resume",
        json={
            "thread_id": "test-thread-123",
            "decision": "reject",
        },
    )

    assert response.status_code == 422


def test_investigate_rejects_short_query():
    response = client.post(
        "/api/v1/investigate",
        json={"query": "Hi"},
    )

    assert response.status_code == 422