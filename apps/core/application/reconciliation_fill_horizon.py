"""Deterministic fill-history horizon for reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from apps.core.ports.reconciliation_snapshot import (
    LocalReconciliationSnapshot,
)
from packages.contracts.primitives import normalize_utc_datetime


class ReconciliationFillHorizonState(StrEnum):
    """Whether a complete venue fill query can be bounded safely."""

    BOUNDED = "BOUNDED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class ReconciliationFillHorizon:
    """Canonical lower bound for venue fill-history collection."""

    state: ReconciliationFillHorizonState
    since: datetime | None

    def __post_init__(self) -> None:
        if not isinstance(
            self.state,
            ReconciliationFillHorizonState,
        ):
            raise ValueError(
                "state must be a ReconciliationFillHorizonState"
            )

        if self.state is ReconciliationFillHorizonState.BOUNDED:
            if self.since is None:
                raise ValueError(
                    "BOUNDED fill horizon requires since"
                )

            object.__setattr__(
                self,
                "since",
                normalize_utc_datetime(
                    self.since,
                    field_name="since",
                ),
            )
            return

        if self.since is not None:
            raise ValueError(
                "UNKNOWN fill horizon must not define since"
            )


def derive_reconciliation_fill_horizon(
    snapshot: LocalReconciliationSnapshot,
) -> ReconciliationFillHorizon:
    """Derive the earliest safe venue fill-history lower bound.

    The local snapshot is historically unbounded for one scope.

    Therefore:
    - earliest local fill execution time is a candidate lower bound;
    - earliest local order creation time is also required so a venue fill
      missing locally can still be discovered;
    - no local orders and no local fills means completeness cannot be proven.
    """

    if not isinstance(
        snapshot,
        LocalReconciliationSnapshot,
    ):
        raise ValueError(
            "snapshot must be a LocalReconciliationSnapshot"
        )

    candidates: list[datetime] = []

    candidates.extend(
        fill.executed_at
        for fill in snapshot.fills
    )

    candidates.extend(
        order.created_at
        for order in snapshot.orders
    )

    if not candidates:
        return ReconciliationFillHorizon(
            state=ReconciliationFillHorizonState.UNKNOWN,
            since=None,
        )

    return ReconciliationFillHorizon(
        state=ReconciliationFillHorizonState.BOUNDED,
        since=min(candidates),
    )
