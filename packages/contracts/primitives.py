"""Canonical NEXUS V2 numeric and time conventions."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal


def require_decimal(
    value: Decimal,
    *,
    field_name: str,
) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be Decimal")

    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")

    return value


def require_positive_decimal(
    value: Decimal,
    *,
    field_name: str,
) -> Decimal:
    value = require_decimal(value, field_name=field_name)

    if value <= 0:
        raise ValueError(f"{field_name} must be positive")

    return value


def require_non_negative_decimal(
    value: Decimal,
    *,
    field_name: str,
) -> Decimal:
    value = require_decimal(value, field_name=field_name)

    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")

    return value


def normalize_utc_datetime(
    value: datetime,
    *,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be datetime")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")

    return value.astimezone(UTC)
