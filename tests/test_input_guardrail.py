from app.guardrails.input_guardrail import (
    validate_input,
    InputGuardrailError,
)


def test_valid_input():
    state = {
        "user_query": "Analyze current project delivery risks."
    }

    result = validate_input(state)

    assert result["user_query"] == (
        "Analyze current project delivery risks."
    )


def test_empty_input():
    state = {
        "user_query": ""
    }

    try:
        validate_input(state)
        assert False
    except InputGuardrailError:
        assert True


def test_whitespace_input():
    state = {
        "user_query": "   "
    }

    try:
        validate_input(state)
        assert False
    except InputGuardrailError:
        assert True


def test_query_too_long():
    state = {
        "user_query": "a" * 2001
    }

    try:
        validate_input(state)
        assert False
    except InputGuardrailError:
        assert True