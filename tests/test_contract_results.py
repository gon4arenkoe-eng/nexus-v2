from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from packages.contracts.results import (
    ErrorInfo,
    Failure,
    Result,
    Success,
)


def test_error_info_preserves_fields() -> None:
    error = ErrorInfo(
        code="ORDER_NOT_FOUND",
        message="Execution order was not found",
        retryable=False,
    )

    assert error.code == "ORDER_NOT_FOUND"
    assert error.message == "Execution order was not found"
    assert error.retryable is False


def test_error_info_trims_required_text() -> None:
    error = ErrorInfo(
        code="  ORDER_NOT_FOUND  ",
        message="  Execution order was not found  ",
    )

    assert error.code == "ORDER_NOT_FOUND"
    assert error.message == "Execution order was not found"


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("code", ""),
        ("code", "   "),
        ("message", ""),
        ("message", "   "),
    ],
)
def test_error_info_rejects_empty_required_text(
    field_name: str,
    value: str,
) -> None:
    values = {
        "code": "ORDER_NOT_FOUND",
        "message": "Execution order was not found",
    }
    values[field_name] = value

    with pytest.raises(ValueError):
        ErrorInfo(**values)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("code", 123),
        ("message", 123),
    ],
)
def test_error_info_rejects_non_string_required_text(
    field_name: str,
    value: object,
) -> None:
    values: dict[str, object] = {
        "code": "ORDER_NOT_FOUND",
        "message": "Execution order was not found",
    }
    values[field_name] = value

    with pytest.raises(ValueError):
        ErrorInfo(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "retryable",
    [0, 1, "false", None],
)
def test_error_info_retryable_must_be_bool(
    retryable: object,
) -> None:
    with pytest.raises(ValueError):
        ErrorInfo(
            code="TEMPORARY_FAILURE",
            message="Temporary failure",
            retryable=retryable,  # type: ignore[arg-type]
        )


def test_error_info_is_frozen() -> None:
    error = ErrorInfo(
        code="ORDER_NOT_FOUND",
        message="Execution order was not found",
    )

    with pytest.raises(FrozenInstanceError):
        error.code = "OTHER"  # type: ignore[misc]


def test_success_preserves_value() -> None:
    result = Success(value=42)

    assert result.value == 42


def test_success_none_is_valid() -> None:
    result = Success[None](value=None)

    assert result.value is None


def test_success_is_frozen() -> None:
    result = Success(value="ok")

    with pytest.raises(FrozenInstanceError):
        result.value = "changed"  # type: ignore[misc]


def test_failure_preserves_error() -> None:
    error = ErrorInfo(
        code="ORDER_NOT_FOUND",
        message="Execution order was not found",
    )

    result = Failure(error=error)

    assert result.error is error


def test_failure_rejects_non_error_info() -> None:
    with pytest.raises(ValueError):
        Failure(error="bad")  # type: ignore[arg-type]


def test_failure_is_frozen() -> None:
    result = Failure(
        error=ErrorInfo(
            code="ORDER_NOT_FOUND",
            message="Execution order was not found",
        )
    )

    with pytest.raises(FrozenInstanceError):
        result.error = ErrorInfo(  # type: ignore[misc]
            code="OTHER",
            message="Other",
        )


def consume_result(result: Result[int]) -> int:
    if isinstance(result, Success):
        return result.value

    return -1


def test_result_alias_accepts_success() -> None:
    assert consume_result(Success(value=7)) == 7


def test_result_alias_accepts_failure() -> None:
    assert (
        consume_result(
            Failure(
                error=ErrorInfo(
                    code="FAILED",
                    message="Operation failed",
                )
            )
        )
        == -1
    )


def test_result_contract_has_no_http_semantics() -> None:
    error = ErrorInfo(
        code="FAILED",
        message="Operation failed",
    )

    assert not hasattr(error, "status_code")
    assert not hasattr(error, "http_status")
    assert not hasattr(error, "headers")
