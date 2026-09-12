"""Tests for canonical Phase 3 reconciliation domain contracts."""

from __future__ import annotations

from datetime import UTC, datetime
import inspect

import pytest

from apps.core.domain.reconciliation import (
    ReconciliationDiscrepancy,
    ReconciliationDiscrepancyKind,
    ReconciliationResult,
    ReconciliationResultState,
    ReconciliationSourceState,
    ReconciliationSubject,
    build_reconciliation_result,
)
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)


VENUE_ID = VenueId("BINANCE")
ACCOUNT_ID = AccountId(
    venue_id=VENUE_ID,
    value=7,
)
INSTRUMENT_ID = InstrumentId(
    venue_id=VENUE_ID,
    native_symbol="BTCUSDT",
    instrument_type=InstrumentType.PERPETUAL,
    asset_class=AssetClass.CRYPTO,
)
NOW = datetime(
    2026,
    9,
    12,
    12,
    0,
    tzinfo=UTC,
)


def _discrepancy(
    *,
    kind: ReconciliationDiscrepancyKind = (
        ReconciliationDiscrepancyKind.ORDER_STATE_DRIFT
    ),
    subject: ReconciliationSubject = ReconciliationSubject.ORDER,
    user_id: int = 11,
    instrument_id: InstrumentId | None = INSTRUMENT_ID,
    local_reference: str | None = "local-1",
    venue_reference: str | None = "venue-1",
    local_value: str | None = "ACCEPTED",
    venue_value: str | None = "FILLED",
) -> ReconciliationDiscrepancy:
    return ReconciliationDiscrepancy(
        kind=kind,
        subject=subject,
        user_id=user_id,
        account_id=ACCOUNT_ID,
        instrument_id=instrument_id,
        observed_at=NOW,
        local_reference=local_reference,
        venue_reference=venue_reference,
        local_value=local_value,
        venue_value=venue_value,
    )


def test_current_without_discrepancies_is_matched() -> None:
    result = build_reconciliation_result(
        user_id=11,
        account_id=ACCOUNT_ID,
        source_state=ReconciliationSourceState.CURRENT,
        observed_at=NOW,
    )

    assert result.state is ReconciliationResultState.MATCHED


def test_current_with_discrepancy_is_not_matched() -> None:
    result = build_reconciliation_result(
        user_id=11,
        account_id=ACCOUNT_ID,
        source_state=ReconciliationSourceState.CURRENT,
        observed_at=NOW,
        discrepancies=(_discrepancy(),),
    )

    assert (
        result.state
        is ReconciliationResultState.DISCREPANCY
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    (
        (
            ReconciliationSourceState.STALE,
            ReconciliationResultState.STALE,
        ),
        (
            ReconciliationSourceState.DEGRADED,
            ReconciliationResultState.DEGRADED,
        ),
        (
            ReconciliationSourceState.UNAVAILABLE,
            ReconciliationResultState.UNAVAILABLE,
        ),
        (
            ReconciliationSourceState.UNKNOWN,
            ReconciliationResultState.UNKNOWN,
        ),
    ),
)
def test_non_current_source_never_becomes_matched(
    source: ReconciliationSourceState,
    expected: ReconciliationResultState,
) -> None:
    result = build_reconciliation_result(
        user_id=11,
        account_id=ACCOUNT_ID,
        source_state=source,
        observed_at=NOW,
    )

    assert result.state is expected


def test_ambiguous_green_state_fails_closed() -> None:
    with pytest.raises(
        ValueError,
        match="contradicts source/discrepancies",
    ):
        ReconciliationResult(
            user_id=11,
            account_id=ACCOUNT_ID,
            source_state=ReconciliationSourceState.STALE,
            state=ReconciliationResultState.MATCHED,
            observed_at=NOW,
            discrepancies=(),
        )


def test_kind_must_match_subject() -> None:
    with pytest.raises(
        ValueError,
        match="does not match subject",
    ):
        _discrepancy(
            subject=ReconciliationSubject.POSITION,
        )


def test_unknown_venue_order_requires_reference() -> None:
    with pytest.raises(
        ValueError,
        match="requires venue_reference",
    ):
        _discrepancy(
            kind=(
                ReconciliationDiscrepancyKind
                .VENUE_ORDER_UNKNOWN_LOCALLY
            ),
            venue_reference=None,
            local_value=None,
            venue_value=None,
        )


def test_missing_local_fill_requires_reference() -> None:
    with pytest.raises(
        ValueError,
        match="missing local fill requires venue_reference",
    ):
        _discrepancy(
            kind=ReconciliationDiscrepancyKind.MISSING_LOCAL_FILL,
            subject=ReconciliationSubject.FILL,
            venue_reference=None,
            local_value=None,
            venue_value=None,
        )


def test_drift_requires_different_values() -> None:
    with pytest.raises(
        ValueError,
        match="drift values must differ",
    ):
        _discrepancy(
            local_value="FILLED",
            venue_value="FILLED",
        )


def test_position_discrepancy_requires_instrument() -> None:
    with pytest.raises(
        ValueError,
        match="requires instrument_id",
    ):
        _discrepancy(
            kind=(
                ReconciliationDiscrepancyKind
                .POSITION_QUANTITY_DRIFT
            ),
            subject=ReconciliationSubject.POSITION,
            instrument_id=None,
            local_value="1",
            venue_value="2",
        )


def test_cross_user_result_fails_closed() -> None:
    discrepancy = _discrepancy(user_id=12)

    with pytest.raises(
        ValueError,
        match="user_id does not match",
    ):
        build_reconciliation_result(
            user_id=11,
            account_id=ACCOUNT_ID,
            source_state=ReconciliationSourceState.CURRENT,
            observed_at=NOW,
            discrepancies=(discrepancy,),
        )


def test_discrepancy_order_is_deterministic() -> None:
    first = _discrepancy()

    second = _discrepancy(
        kind=(
            ReconciliationDiscrepancyKind
            .POSITION_QUANTITY_DRIFT
        ),
        subject=ReconciliationSubject.POSITION,
        local_reference=None,
        venue_reference=None,
        local_value="1",
        venue_value="2",
    )

    a = build_reconciliation_result(
        user_id=11,
        account_id=ACCOUNT_ID,
        source_state=ReconciliationSourceState.CURRENT,
        observed_at=NOW,
        discrepancies=(second, first),
    )

    b = build_reconciliation_result(
        user_id=11,
        account_id=ACCOUNT_ID,
        source_state=ReconciliationSourceState.CURRENT,
        observed_at=NOW,
        discrepancies=(first, second),
    )

    assert a == b


def test_duplicate_discrepancy_fails_closed() -> None:
    discrepancy = _discrepancy()

    with pytest.raises(
        ValueError,
        match="duplicate discrepancy",
    ):
        build_reconciliation_result(
            user_id=11,
            account_id=ACCOUNT_ID,
            source_state=ReconciliationSourceState.CURRENT,
            observed_at=NOW,
            discrepancies=(
                discrepancy,
                discrepancy,
            ),
        )


def test_source_discrepancy_cannot_contradict_source() -> None:
    discrepancy = _discrepancy(
        kind=ReconciliationDiscrepancyKind.SOURCE_STALE,
        subject=ReconciliationSubject.SOURCE,
        instrument_id=None,
        local_reference=None,
        venue_reference=None,
        local_value=None,
        venue_value=None,
    )

    with pytest.raises(
        ValueError,
        match="contradicts source_state",
    ):
        build_reconciliation_result(
            user_id=11,
            account_id=ACCOUNT_ID,
            source_state=ReconciliationSourceState.DEGRADED,
            observed_at=NOW,
            discrepancies=(discrepancy,),
        )


def test_required_discrepancy_classes_exist() -> None:
    expected = {
        "LOCAL_ORDER_MISSING_ON_VENUE",
        "VENUE_ORDER_UNKNOWN_LOCALLY",
        "ORDER_STATE_DRIFT",
        "MISSING_LOCAL_FILL",
        "DUPLICATE_OR_REPLAYED_FILL",
        "LOCAL_POSITION_MISSING_ON_VENUE",
        "VENUE_POSITION_MISSING_LOCALLY",
        "POSITION_QUANTITY_DRIFT",
        "POSITION_SIDE_DRIFT",
        "POSITION_ENTRY_PRICE_DRIFT",
        "ACCOUNT_BALANCE_STALE",
        "ACCOUNT_BALANCE_UNAVAILABLE",
        "SOURCE_STALE",
        "SOURCE_DEGRADED",
        "SOURCE_UNAVAILABLE",
        "SOURCE_UNKNOWN",
    }

    assert {
        item.value
        for item in ReconciliationDiscrepancyKind
    } == expected


def test_domain_has_no_runtime_authority() -> None:
    import apps.core.domain.reconciliation as reconciliation

    source = inspect.getsource(reconciliation)

    forbidden = (
        "apps.core.ports",
        "VenueAdapter",
        "sqlalchemy",
        "AsyncSession",
        "submit_order",
        "cancel_order",
        "ExecutionCoordinator",
    )

    assert not any(
        value in source
        for value in forbidden
    )
