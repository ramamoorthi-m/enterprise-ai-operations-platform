import logging
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from google.genai.errors import APIError as GeminiAPIError
from langgraph.types import Command
from pydantic import BaseModel, Field

from app.config.settings import settings
from app.workflow.graph import graph


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enterprise AI Operations Platform",
    version="0.3.0",
)


class InvestigationRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)
    project: str | None = Field(default=None, min_length=1, max_length=100)


class ResumeRequest(BaseModel):
    thread_id: str = Field(..., min_length=1)
    decision: Literal["approve", "retry"]


class InvestigationResponse(BaseModel):
    thread_id: str
    status: str
    evaluation_passed: bool
    confidence: float
    human_review_required: bool
    human_review_reason: str
    review_payload: dict[str, Any]
    plan: list[dict[str, Any]]
    investigation_history: list[dict[str, Any]]
    analysis: dict[str, Any]
    final_report: str
    errors: list[Any]


def build_response(
    result: dict[str, Any],
    thread_id: str,
) -> InvestigationResponse:
    interrupts = result.get("__interrupt__", ())
    review_payload: dict[str, Any] = {}

    if interrupts:
        interrupt_value = getattr(interrupts[0], "value", {})
        if isinstance(interrupt_value, dict):
            review_payload = interrupt_value

    paused_for_review = bool(interrupts)

    return InvestigationResponse(
        thread_id=thread_id,
        status=(
            "awaiting_human_review"
            if paused_for_review
            else result.get("status", "")
        ),
        evaluation_passed=result.get("evaluation_passed", False),
        confidence=result.get("confidence", 0.0),
        human_review_required=(
            paused_for_review
            or result.get("human_review_required", False)
        ),
        human_review_reason=(
            review_payload.get("reason")
            or result.get("human_review_reason", "")
        ),
        review_payload=review_payload,
        plan=result.get("plan", []),
        investigation_history=result.get("investigation_history", []),
        analysis=result.get("analysis", {}),
        final_report=result.get("report", ""),
        errors=result.get("errors", []),
    )


@app.get("/")
async def root():
    return {
        "message": "Enterprise AI Operations Platform is running!"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "enterprise-ai-operations-platform",
    }


@app.post(
    "/api/v1/investigate",
    response_model=InvestigationResponse,
)
async def investigate(request: InvestigationRequest):
    thread_id = str(uuid4())
    project = request.project or settings.jira_project_key

    initial_state = {
        "user_query": request.query,
        "project": project,
        "plan": [],
        "required_sources": [],
        "github_data": {},
        "jira_data": {},
        "doc_data": {},
        "slack_data": {},
        "findings": [],
        "report": "",
        "confidence": 0.0,
        "human_review_required": False,
        "human_review_reason": "",
        "errors": [],
        "failures": [],
        "status": "started",
        "evaluation_passed": False,
        "retry_required": False,
        "retry_count": 0,
        "max_retries": 2,
    }

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    try:
        result = await graph.ainvoke(initial_state, config=config)
        return build_response(result, thread_id)

    except GeminiAPIError as exc:
        logger.exception(
            "Gemini API request failed; thread_id=%s",
            thread_id,
        )

        status_code = getattr(exc, "code", None)

        if status_code == 429:
            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini quota or rate limit exceeded. "
                    "Check your Gemini API quota and retry availability."
                ),
            ) from None

        if status_code == 503:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Gemini is temporarily unavailable. "
                    "Please try again later."
                ),
            ) from None

        raise HTTPException(
            status_code=502,
            detail=(
                "The Gemini provider request failed. "
                f"Provider status: {status_code or 'unknown'}. "
                "Check backend logs for details."
            ),
        ) from None

    except Exception as exc:
        logger.exception(
            "Investigation workflow failed; thread_id=%s",
            thread_id,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Investigation workflow failed "
                f"({type(exc).__name__}). "
                f"Reference: {thread_id}. "
                "Check backend logs for details."
            ),
        ) from None


@app.post(
    "/api/v1/investigate/resume",
    response_model=InvestigationResponse,
)
async def resume_investigation(request: ResumeRequest):
    config = {
        "configurable": {
            "thread_id": request.thread_id,
        }
    }

    try:
        snapshot = await graph.aget_state(config)

        is_paused_for_review = any(
            getattr(task, "interrupts", ())
            for task in snapshot.tasks
        )

        if not is_paused_for_review:
            raise HTTPException(
                status_code=409,
                detail="This investigation is not paused for human review.",
            )

        result = await graph.ainvoke(
            Command(resume=request.decision),
            config=config,
        )

        return build_response(result, request.thread_id)

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to resume investigation; thread_id=%s",
            request.thread_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to resume investigation.",
        ) from None