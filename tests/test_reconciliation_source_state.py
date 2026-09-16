"""Tests for deterministic reconciliation source-quality composition."""

from __future__ import annotations

import pytest

from apps.core.application.reconciliation_source_state import (
    compose_reconciliation_source_state,
    source_state_from_account_observation,
)
from apps.core.domain.reconciliation import (
    ReconciliationSourceState,
)
from apps.core.ports.venue_account import (
    VenueAccountObservationState,
)


CURRENT = ReconciliationSourceState.CURRENT
STALE = ReconciliationSourceState.STALE
DEGRADED = ReconciliationSourceState.DEGRADED
UNAVAILABLE = ReconciliationSourceState.UNAVAILABLE
UNKNOWN = ReconciliationSourceState.UNKNOWN


def compose(
    *,
    orders: ReconciliationSourceState = CURRENT,
    fills: ReconciliationSourceState = CURRENT,
    positions: ReconciliationSourceState = CURRENT,
    account: ReconciliationSourceState = CURRENT,
) -> ReconciliationSourceState:
    return compose_reconciliation_source_state(
        orders=orders,
        fills=fills,
        positions=positions,
        account=account,
    )


def test_all_required_observations_current() -> None:
    assert compose() is CURRENT


def test_known_stale_observation_makes_source_stale() -> None:
    assert compose(fills=STALE) is STALE


def test_explicit_degradation_dominates_stale() -> None:
    assert compose(
        orders=STALE,
        fills=DEGRADED,
    ) is DEGRADED


def test_partial_unavailability_is_degraded() -> None:
    assert compose(
        positions=UNAVAILABLE,
    ) is DEGRADED


def test_all_required_observations_unavailable() -> None:
    assert compose(
        orders=UNAVAILABLE,
        fills=UNAVAILABLE,
        positions=UNAVAILABLE,
        account=UNAVAILABLE,
    ) is UNAVAILABLE


def test_unknown_dominates_other_quality_states() -> None:
    assert compose(
        orders=UNAVAILABLE,
        fills=UNKNOWN,
        positions=STALE,
    ) is UNKNOWN


@pytest.mark.parametrize(
    ("account_state", "expected"),
    (
        (
            VenueAccountObservationState.CURRENT,
            CURRENT,
        ),
        (
            VenueAccountObservationState.STALE,
            STALE,
        ),
        (
            VenueAccountObservationState.UNAVAILABLE,
            UNAVAILABLE,
        ),
    ),
)
def test_account_observation_projection(
    account_state: VenueAccountObservationState,
    expected: ReconciliationSourceState,
) -> None:
    assert (
        source_state_from_account_observation(
            account_state
        )
        is expected
    )


def test_composition_rejects_noncanonical_state() -> None:
    with pytest.raises(
        ValueError,
        match="ReconciliationSourceState",
    ):
        compose_reconciliation_source_state(
            orders=CURRENT,
            fills=CURRENT,
            positions=CURRENT,
            account="CURRENT",  # type: ignore[arg-type]
        )
