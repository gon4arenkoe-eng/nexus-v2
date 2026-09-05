from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from packages.contracts.primitives import (
    normalize_utc_datetime,
    require_decimal,
    require_non_negative_decimal,
    require_positive_decimal,
)


def test_require_decimal_accepts_decimal() -> None:
    value = Decimal("1.23456789")

    assert require_decimal(value, field_name="quantity") is value


@pytest.mark.parametrize("value", [1, 1.0, "1.0", True])
def test_require_decimal_rejects_non_decimal(value: object) -> None:
    with pytest.raises(ValueError):
        require_decimal(value, field_name="quantity")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    [
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ],
)
def test_require_decimal_rejects_non_finite(value: Decimal) -> None:
    with pytest.raises(ValueError):
        require_decimal(value, field_name="price")


def test_positive_decimal_accepts_positive_value() -> None:
    value = Decimal("0.00000001")

    assert require_positive_decimal(
        value,
        field_name="quantity",
    ) == value


@pytest.mark.parametrize(
    "value",
    [
        Decimal("0"),
        Decimal("-0.00000001"),
    ],
)
def test_positive_decimal_rejects_zero_and_negative(
    value: Decimal,
) -> None:
    with pytest.raises(ValueError):
        require_positive_decimal(value, field_name="quantity")


def test_non_negative_decimal_accepts_zero() -> None:
    assert require_non_negative_decimal(
        Decimal("0"),
        field_name="fee",
    ) == Decimal("0")


def test_non_negative_decimal_accepts_positive_value() -> None:
    assert require_non_negative_decimal(
        Decimal("1.25"),
        field_name="fee",
    ) == Decimal("1.25")


def test_non_negative_decimal_rejects_negative_value() -> None:
    with pytest.raises(ValueError):
        require_non_negative_decimal(
            Decimal("-0.01"),
            field_name="fee",
        )


def test_utc_datetime_remains_utc() -> None:
    value = datetime(2026, 9, 5, 12, 0, tzinfo=UTC)

    assert normalize_utc_datetime(
        value,
        field_name="occurred_at",
    ) == value


def test_aware_datetime_is_normalized_to_utc() -> None:
    source_tz = timezone(timedelta(hours=3))
    value = datetime(2026, 9, 5, 15, 0, tzinfo=source_tz)

    result = normalize_utc_datetime(
        value,
        field_name="occurred_at",
    )

    assert result == datetime(2026, 9, 5, 12, 0, tzinfo=UTC)
    assert result.tzinfo is UTC


def test_naive_datetime_fails_closed() -> None:
    value = datetime(2026, 9, 5, 12, 0)

    with pytest.raises(ValueError):
        normalize_utc_datetime(
            value,
            field_name="occurred_at",
        )


def test_datetime_type_is_required() -> None:
    with pytest.raises(ValueError):
        normalize_utc_datetime(
            "2026-09-05T12:00:00Z",  # type: ignore[arg-type]
            field_name="occurred_at",
        )
