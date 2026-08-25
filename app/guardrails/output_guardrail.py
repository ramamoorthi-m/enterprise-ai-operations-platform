from typing import Any


class OutputGuardrailError(ValueError):
    """Raised when generated output violates output constraints."""


REQUIRED_REPORT_SECTIONS = [
    "# Enterprise Project Investigation Report",
    "## Investigation Request",
    "## Executive Summary",
    "## Key Findings",
    "## Risks",
    "## Evidence Gaps",
    "## Confidence",
]


FORBIDDEN_OUTPUT_TERMS = [
    "api_key",
    "secret_key",
    "access_token",
    "authorization:",
    "password",
]


FORBIDDEN_INTERNAL_TERMS = [
    "system prompt",
    "developer prompt",
    "tool_map",
    "generate_with_tools",
]


def validate_report_output(
    report: str,
    state: dict[str, Any],
) -> None:
    """Validate the final report before it leaves the workflow."""

    if not isinstance(report, str):
        raise OutputGuardrailError(
            "Generated report must be a string."
        )

    report = report.strip()

    if not report:
        raise OutputGuardrailError(
            "Generated report is empty."
        )

    report_lower = report.lower()

    # ---------------------------------------------------------
    # Required report structure
    # ---------------------------------------------------------

    missing_sections = [
        section
        for section in REQUIRED_REPORT_SECTIONS
        if section.lower() not in report_lower
    ]

    if missing_sections:
        raise OutputGuardrailError(
            "Generated report is missing required sections: "
            f"{missing_sections}"
        )

    # ---------------------------------------------------------
    # Sensitive information protection
    # ---------------------------------------------------------

    leaked_terms = [
        term
        for term in FORBIDDEN_OUTPUT_TERMS
        if term.lower() in report_lower
    ]

    if leaked_terms:
        raise OutputGuardrailError(
            "Generated report contains potentially sensitive "
            "information."
        )

    # ---------------------------------------------------------
    # Internal implementation protection
    # ---------------------------------------------------------

    leaked_internal_terms = [
        term
        for term in FORBIDDEN_INTERNAL_TERMS
        if term.lower() in report_lower
    ]

    if leaked_internal_terms:
        raise OutputGuardrailError(
            "Generated report contains internal implementation "
            "details."
        )