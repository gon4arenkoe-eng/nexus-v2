"""Canonical NEXUS V2 shared result contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeAlias, TypeVar


ValueT = TypeVar("ValueT")


def _required_text(
    value: str,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")

    return normalized


@dataclass(frozen=True, slots=True)
class ErrorInfo:
    code: str
    message: str
    retryable: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "code",
            _required_text(self.code, field_name="code"),
        )
        object.__setattr__(
            self,
            "message",
            _required_text(self.message, field_name="message"),
        )

        if not isinstance(self.retryable, bool):
            raise ValueError("retryable must be bool")


@dataclass(frozen=True, slots=True)
class Success(Generic[ValueT]):
    value: ValueT


@dataclass(frozen=True, slots=True)
class Failure:
    error: ErrorInfo

    def __post_init__(self) -> None:
        if not isinstance(self.error, ErrorInfo):
            raise ValueError("error must be ErrorInfo")


Result: TypeAlias = Success[ValueT] | Failure
