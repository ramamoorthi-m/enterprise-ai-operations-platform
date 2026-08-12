from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    """Structured output produced by the Analysis Agent."""

    summary: str

    key_findings: list[str] = Field(
        default_factory=list
    )

    risks: list[str] = Field(
        default_factory=list
    )

    evidence_gaps: list[str] = Field(
        default_factory=list
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    assessment: str