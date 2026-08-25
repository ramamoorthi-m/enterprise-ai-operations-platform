import pytest

from app.guardrails.output_guardrail import (
    OutputGuardrailError,
    validate_report_output,
)


VALID_REPORT = """
# Enterprise Project Investigation Report

## Investigation Request

Analyze the current project status and identify potential delivery blockers.

## Executive Summary

The investigation collected sufficient evidence to assess the current project status.

## Key Findings

- Jira contains one overdue task.
- GitHub deployment status is available.

## Risks

- One overdue Jira task requires attention.

## Evidence Gaps

No significant evidence gaps were identified.

## Confidence

0.90
"""


@pytest.fixture
def state():
    return {
        "project": "SCRUM",
        "user_query": (
            "Analyze the current project status "
            "and identify potential delivery blockers."
        ),
    }


def test_valid_report_passes(state):

    # Should not raise any exception.
    validate_report_output(
        report=VALID_REPORT,
        state=state,
    )


def test_empty_report_is_rejected(state):

    with pytest.raises(
        OutputGuardrailError,
        match="Generated report is empty",
    ):
        validate_report_output(
            report="",
            state=state,
        )


def test_missing_required_section_is_rejected(state):

    invalid_report = VALID_REPORT.replace(
        "## Evidence Gaps",
        "",
    )

    with pytest.raises(
        OutputGuardrailError,
        match="missing required sections",
    ):
        validate_report_output(
            report=invalid_report,
            state=state,
        )


def test_sensitive_information_is_rejected(state):

    invalid_report = (
        VALID_REPORT
        + "\nThe access_token was exposed during investigation."
    )

    with pytest.raises(
        OutputGuardrailError,
        match="potentially sensitive information",
    ):
        validate_report_output(
            report=invalid_report,
            state=state,
        )


def test_internal_implementation_details_are_rejected(state):

    invalid_report = (
        VALID_REPORT
        + "\nThe system prompt instructed generate_with_tools to execute the investigation."
    )

    with pytest.raises(
        OutputGuardrailError,
        match="internal implementation details",
    ):
        validate_report_output(
            report=invalid_report,
            state=state,
        )


def test_non_string_report_is_rejected(state):

    with pytest.raises(
        OutputGuardrailError,
        match="must be a string",
    ):
        validate_report_output(
            report=None,
            state=state,
        )