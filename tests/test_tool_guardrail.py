import pytest

from app.guardrails.tool_guardrail import (
    ToolGuardrailError,
    validate_tool_call,
)


AVAILABLE_TOOLS = {
    "jira_get_overdue_tasks": object(),
    "github_get_deployment_status": object(),
}


def test_valid_jira_tool_call():

    validate_tool_call(
        tool_name="jira_get_overdue_tasks",
        arguments={"project": "SCRUM"},
        available_tools=AVAILABLE_TOOLS,
    )


def test_unknown_tool_is_blocked():

    with pytest.raises(ToolGuardrailError):

        validate_tool_call(
            tool_name="delete_production_database",
            arguments={},
            available_tools=AVAILABLE_TOOLS,
        )


def test_missing_required_argument_is_blocked():

    with pytest.raises(ToolGuardrailError):

        validate_tool_call(
            tool_name="github_get_deployment_status",
            arguments={},
            available_tools=AVAILABLE_TOOLS,
        )


def test_non_dict_arguments_are_blocked():

    with pytest.raises(ToolGuardrailError):

        validate_tool_call(
            tool_name="jira_get_overdue_tasks",
            arguments=[],
            available_tools=AVAILABLE_TOOLS,
        )