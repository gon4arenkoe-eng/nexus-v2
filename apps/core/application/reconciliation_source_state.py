"""Deterministic reconciliation source-quality composition."""

from __future__ import annotations

from apps.core.domain.reconciliation import (
    ReconciliationSourceState,
)
from apps.core.ports.venue_account import (
    VenueAccountObservationState,
)


def source_state_from_account_observation(
    state: VenueAccountObservationState,
) -> ReconciliationSourceState:
    """Project canonical account observation quality into source quality."""

    if not isinstance(
        state,
        VenueAccountObservationState,
    ):
        raise ValueError(
            "state must be a VenueAccountObservationState"
        )

    mapping = {
        VenueAccountObservationState.CURRENT:
            ReconciliationSourceState.CURRENT,
        VenueAccountObservationState.STALE:
            ReconciliationSourceState.STALE,
        VenueAccountObservationState.UNAVAILABLE:
            ReconciliationSourceState.UNAVAILABLE,
    }

    return mapping[state]


def compose_reconciliation_source_state(
    *,
    orders: ReconciliationSourceState,
    fills: ReconciliationSourceState,
    positions: ReconciliationSourceState,
    account: ReconciliationSourceState,
) -> ReconciliationSourceState:
    """Return one fail-closed quality state for required venue truth.

    Precedence is deterministic:

    UNKNOWN -> DEGRADED -> STALE -> CURRENT, with UNAVAILABLE handled
    specially: every required leg unavailable means UNAVAILABLE, while a
    partial outage means DEGRADED.
    """

    states = (
        orders,
        fills,
        positions,
        account,
    )

    for state in states:
        if not isinstance(
            state,
            ReconciliationSourceState,
        ):
            raise ValueError(
                "all observation states must be "
                "ReconciliationSourceState values"
            )

    if ReconciliationSourceState.UNKNOWN in states:
        return ReconciliationSourceState.UNKNOWN

    unavailable_count = sum(
        state is ReconciliationSourceState.UNAVAILABLE
        for state in states
    )

    if unavailable_count == len(states):
        return ReconciliationSourceState.UNAVAILABLE

    if unavailable_count:
        return ReconciliationSourceState.DEGRADED

    if ReconciliationSourceState.DEGRADED in states:
        return ReconciliationSourceState.DEGRADED

    if ReconciliationSourceState.STALE in states:
        return ReconciliationSourceState.STALE

    return ReconciliationSourceState.CURRENT
