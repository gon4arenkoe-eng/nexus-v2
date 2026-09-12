"""Canonical deterministic reconciliation state and discrepancy model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from packages.contracts.identities import (
    AccountId,
    InstrumentId,
)
from packages.contracts.primitives import normalize_utc_datetime


class ReconciliationSourceState(StrEnum):
    """Availability and quality of observed venue truth."""

    CURRENT = "CURRENT"
    STALE = "STALE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class ReconciliationResultState(StrEnum):
    """Visible outcome of one reconciliation pass."""

    MATCHED = "MATCHED"
    DISCREPANCY = "DISCREPANCY"
    STALE = "STALE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class ReconciliationSubject(StrEnum):
    ORDER = "ORDER"
    FILL = "FILL"
    POSITION = "POSITION"
    ACCOUNT = "ACCOUNT"
    SOURCE = "SOURCE"


class ReconciliationDiscrepancyKind(StrEnum):
    LOCAL_ORDER_MISSING_ON_VENUE = (
        "LOCAL_ORDER_MISSING_ON_VENUE"
    )
    VENUE_ORDER_UNKNOWN_LOCALLY = (
        "VENUE_ORDER_UNKNOWN_LOCALLY"
    )
    ORDER_STATE_DRIFT = "ORDER_STATE_DRIFT"

    MISSING_LOCAL_FILL = "MISSING_LOCAL_FILL"
    DUPLICATE_OR_REPLAYED_FILL = (
        "DUPLICATE_OR_REPLAYED_FILL"
    )

    LOCAL_POSITION_MISSING_ON_VENUE = (
        "LOCAL_POSITION_MISSING_ON_VENUE"
    )
    VENUE_POSITION_MISSING_LOCALLY = (
        "VENUE_POSITION_MISSING_LOCALLY"
    )
    POSITION_QUANTITY_DRIFT = "POSITION_QUANTITY_DRIFT"
    POSITION_SIDE_DRIFT = "POSITION_SIDE_DRIFT"
    POSITION_ENTRY_PRICE_DRIFT = (
        "POSITION_ENTRY_PRICE_DRIFT"
    )

    ACCOUNT_BALANCE_STALE = "ACCOUNT_BALANCE_STALE"
    ACCOUNT_BALANCE_UNAVAILABLE = (
        "ACCOUNT_BALANCE_UNAVAILABLE"
    )

    SOURCE_STALE = "SOURCE_STALE"
    SOURCE_DEGRADED = "SOURCE_DEGRADED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    SOURCE_UNKNOWN = "SOURCE_UNKNOWN"


_KIND_SUBJECT = {
    ReconciliationDiscrepancyKind.LOCAL_ORDER_MISSING_ON_VENUE:
        ReconciliationSubject.ORDER,
    ReconciliationDiscrepancyKind.VENUE_ORDER_UNKNOWN_LOCALLY:
        ReconciliationSubject.ORDER,
    ReconciliationDiscrepancyKind.ORDER_STATE_DRIFT:
        ReconciliationSubject.ORDER,
    ReconciliationDiscrepancyKind.MISSING_LOCAL_FILL:
        ReconciliationSubject.FILL,
    ReconciliationDiscrepancyKind.DUPLICATE_OR_REPLAYED_FILL:
        ReconciliationSubject.FILL,
    ReconciliationDiscrepancyKind.LOCAL_POSITION_MISSING_ON_VENUE:
        ReconciliationSubject.POSITION,
    ReconciliationDiscrepancyKind.VENUE_POSITION_MISSING_LOCALLY:
        ReconciliationSubject.POSITION,
    ReconciliationDiscrepancyKind.POSITION_QUANTITY_DRIFT:
        ReconciliationSubject.POSITION,
    ReconciliationDiscrepancyKind.POSITION_SIDE_DRIFT:
        ReconciliationSubject.POSITION,
    ReconciliationDiscrepancyKind.POSITION_ENTRY_PRICE_DRIFT:
        ReconciliationSubject.POSITION,
    ReconciliationDiscrepancyKind.ACCOUNT_BALANCE_STALE:
        ReconciliationSubject.ACCOUNT,
    ReconciliationDiscrepancyKind.ACCOUNT_BALANCE_UNAVAILABLE:
        ReconciliationSubject.ACCOUNT,
    ReconciliationDiscrepancyKind.SOURCE_STALE:
        ReconciliationSubject.SOURCE,
    ReconciliationDiscrepancyKind.SOURCE_DEGRADED:
        ReconciliationSubject.SOURCE,
    ReconciliationDiscrepancyKind.SOURCE_UNAVAILABLE:
        ReconciliationSubject.SOURCE,
    ReconciliationDiscrepancyKind.SOURCE_UNKNOWN:
        ReconciliationSubject.SOURCE,
}


_NON_CURRENT_RESULTS = {
    ReconciliationSourceState.STALE:
        ReconciliationResultState.STALE,
    ReconciliationSourceState.DEGRADED:
        ReconciliationResultState.DEGRADED,
    ReconciliationSourceState.UNAVAILABLE:
        ReconciliationResultState.UNAVAILABLE,
    ReconciliationSourceState.UNKNOWN:
        ReconciliationResultState.UNKNOWN,
}


_SOURCE_KIND_STATE = {
    ReconciliationDiscrepancyKind.SOURCE_STALE:
        ReconciliationSourceState.STALE,
    ReconciliationDiscrepancyKind.SOURCE_DEGRADED:
        ReconciliationSourceState.DEGRADED,
    ReconciliationDiscrepancyKind.SOURCE_UNAVAILABLE:
        ReconciliationSourceState.UNAVAILABLE,
    ReconciliationDiscrepancyKind.SOURCE_UNKNOWN:
        ReconciliationSourceState.UNKNOWN,
}


_DRIFT_KINDS = frozenset(
    {
        ReconciliationDiscrepancyKind.ORDER_STATE_DRIFT,
        ReconciliationDiscrepancyKind.POSITION_QUANTITY_DRIFT,
        ReconciliationDiscrepancyKind.POSITION_SIDE_DRIFT,
        ReconciliationDiscrepancyKind.POSITION_ENTRY_PRICE_DRIFT,
    }
)


_INSTRUMENT_KINDS = frozenset(
    {
        ReconciliationDiscrepancyKind.LOCAL_ORDER_MISSING_ON_VENUE,
        ReconciliationDiscrepancyKind.VENUE_ORDER_UNKNOWN_LOCALLY,
        ReconciliationDiscrepancyKind.ORDER_STATE_DRIFT,
        ReconciliationDiscrepancyKind.MISSING_LOCAL_FILL,
        ReconciliationDiscrepancyKind.DUPLICATE_OR_REPLAYED_FILL,
        ReconciliationDiscrepancyKind.LOCAL_POSITION_MISSING_ON_VENUE,
        ReconciliationDiscrepancyKind.VENUE_POSITION_MISSING_LOCALLY,
        ReconciliationDiscrepancyKind.POSITION_QUANTITY_DRIFT,
        ReconciliationDiscrepancyKind.POSITION_SIDE_DRIFT,
        ReconciliationDiscrepancyKind.POSITION_ENTRY_PRICE_DRIFT,
    }
)


def _require_user_id(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("user_id must be an integer")

    if value <= 0:
        raise ValueError("user_id must be positive")

    return value


def _optional_text(
    value: str | None,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")

    return normalized


@dataclass(frozen=True, slots=True)
class ReconciliationDiscrepancy:
    """Immutable canonical discrepancy evidence."""

    kind: ReconciliationDiscrepancyKind
    subject: ReconciliationSubject
    user_id: int
    account_id: AccountId
    observed_at: datetime
    instrument_id: InstrumentId | None = None
    local_reference: str | None = None
    venue_reference: str | None = None
    local_value: str | None = None
    venue_value: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.kind,
            ReconciliationDiscrepancyKind,
        ):
            raise ValueError(
                "kind must be a ReconciliationDiscrepancyKind"
            )

        if not isinstance(
            self.subject,
            ReconciliationSubject,
        ):
            raise ValueError(
                "subject must be a ReconciliationSubject"
            )

        if self.subject is not _KIND_SUBJECT[self.kind]:
            raise ValueError(
                "discrepancy kind does not match subject"
            )

        user_id = _require_user_id(self.user_id)

        if not isinstance(self.account_id, AccountId):
            raise ValueError(
                "account_id must be an AccountId"
            )

        instrument_id = self.instrument_id

        if instrument_id is not None:
            if not isinstance(instrument_id, InstrumentId):
                raise ValueError(
                    "instrument_id must be an InstrumentId"
                )

            if (
                instrument_id.venue_id
                != self.account_id.venue_id
            ):
                raise ValueError(
                    "account venue must match instrument venue"
                )

        if (
            self.kind in _INSTRUMENT_KINDS
            and instrument_id is None
        ):
            raise ValueError(
                "discrepancy kind requires instrument_id"
            )

        local_reference = _optional_text(
            self.local_reference,
            field_name="local_reference",
        )
        venue_reference = _optional_text(
            self.venue_reference,
            field_name="venue_reference",
        )
        local_value = _optional_text(
            self.local_value,
            field_name="local_value",
        )
        venue_value = _optional_text(
            self.venue_value,
            field_name="venue_value",
        )

        if (
            self.kind
            is ReconciliationDiscrepancyKind
            .LOCAL_ORDER_MISSING_ON_VENUE
            and local_reference is None
        ):
            raise ValueError(
                "local missing order requires local_reference"
            )

        if (
            self.kind
            is ReconciliationDiscrepancyKind
            .VENUE_ORDER_UNKNOWN_LOCALLY
            and venue_reference is None
        ):
            raise ValueError(
                "unknown venue order requires venue_reference"
            )

        if (
            self.kind
            is ReconciliationDiscrepancyKind.MISSING_LOCAL_FILL
            and venue_reference is None
        ):
            raise ValueError(
                "missing local fill requires venue_reference"
            )

        if (
            self.kind
            is ReconciliationDiscrepancyKind
            .DUPLICATE_OR_REPLAYED_FILL
            and local_reference is None
            and venue_reference is None
        ):
            raise ValueError(
                "duplicate fill requires a stable reference"
            )

        if self.kind in _DRIFT_KINDS:
            if local_value is None or venue_value is None:
                raise ValueError(
                    "drift discrepancy requires local and venue values"
                )

            if local_value == venue_value:
                raise ValueError(
                    "drift values must differ"
                )

        object.__setattr__(
            self,
            "user_id",
            user_id,
        )
        object.__setattr__(
            self,
            "observed_at",
            normalize_utc_datetime(
                self.observed_at,
                field_name="observed_at",
            ),
        )
        object.__setattr__(
            self,
            "local_reference",
            local_reference,
        )
        object.__setattr__(
            self,
            "venue_reference",
            venue_reference,
        )
        object.__setattr__(
            self,
            "local_value",
            local_value,
        )
        object.__setattr__(
            self,
            "venue_value",
            venue_value,
        )


def reconciliation_discrepancy_key(
    discrepancy: ReconciliationDiscrepancy,
) -> tuple[str, ...]:
    instrument = discrepancy.instrument_id

    instrument_key = ""

    if instrument is not None:
        instrument_key = "|".join(
            (
                str(instrument.venue_id),
                instrument.native_symbol,
                instrument.instrument_type.value,
                instrument.asset_class.value,
            )
        )

    return (
        discrepancy.kind.value,
        discrepancy.subject.value,
        str(discrepancy.user_id),
        str(discrepancy.account_id.venue_id),
        str(discrepancy.account_id.value),
        instrument_key,
        discrepancy.local_reference or "",
        discrepancy.venue_reference or "",
        discrepancy.local_value or "",
        discrepancy.venue_value or "",
        discrepancy.observed_at.isoformat(),
    )


def _result_state(
    source_state: ReconciliationSourceState,
    *,
    has_discrepancies: bool,
) -> ReconciliationResultState:
    if source_state is not ReconciliationSourceState.CURRENT:
        return _NON_CURRENT_RESULTS[source_state]

    if has_discrepancies:
        return ReconciliationResultState.DISCREPANCY

    return ReconciliationResultState.MATCHED


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    """Deterministic account-scoped reconciliation result."""

    user_id: int
    account_id: AccountId
    source_state: ReconciliationSourceState
    state: ReconciliationResultState
    observed_at: datetime
    discrepancies: tuple[ReconciliationDiscrepancy, ...]

    def __post_init__(self) -> None:
        user_id = _require_user_id(self.user_id)

        if not isinstance(self.account_id, AccountId):
            raise ValueError(
                "account_id must be an AccountId"
            )

        if not isinstance(
            self.source_state,
            ReconciliationSourceState,
        ):
            raise ValueError(
                "source_state must be a ReconciliationSourceState"
            )

        if not isinstance(
            self.state,
            ReconciliationResultState,
        ):
            raise ValueError(
                "state must be a ReconciliationResultState"
            )

        if not isinstance(self.discrepancies, tuple):
            raise ValueError(
                "discrepancies must be a tuple"
            )

        for discrepancy in self.discrepancies:
            if not isinstance(
                discrepancy,
                ReconciliationDiscrepancy,
            ):
                raise ValueError(
                    "discrepancies must contain "
                    "ReconciliationDiscrepancy values"
                )

        ordered = tuple(
            sorted(
                self.discrepancies,
                key=reconciliation_discrepancy_key,
            )
        )

        keys = tuple(
            reconciliation_discrepancy_key(item)
            for item in ordered
        )

        if len(keys) != len(set(keys)):
            raise ValueError(
                "duplicate discrepancy in reconciliation result"
            )

        for discrepancy in ordered:
            if discrepancy.user_id != user_id:
                raise ValueError(
                    "discrepancy user_id does not match result"
                )

            if discrepancy.account_id != self.account_id:
                raise ValueError(
                    "discrepancy account_id does not match result"
                )

            required_source = _SOURCE_KIND_STATE.get(
                discrepancy.kind
            )

            if (
                required_source is not None
                and required_source is not self.source_state
            ):
                raise ValueError(
                    "source discrepancy contradicts source_state"
                )

        expected = _result_state(
            self.source_state,
            has_discrepancies=bool(ordered),
        )

        if self.state is not expected:
            raise ValueError(
                "reconciliation state contradicts "
                "source/discrepancies"
            )

        object.__setattr__(
            self,
            "user_id",
            user_id,
        )
        object.__setattr__(
            self,
            "observed_at",
            normalize_utc_datetime(
                self.observed_at,
                field_name="observed_at",
            ),
        )
        object.__setattr__(
            self,
            "discrepancies",
            ordered,
        )


def build_reconciliation_result(
    *,
    user_id: int,
    account_id: AccountId,
    source_state: ReconciliationSourceState,
    observed_at: datetime,
    discrepancies: tuple[ReconciliationDiscrepancy, ...] = (),
) -> ReconciliationResult:
    state = _result_state(
        source_state,
        has_discrepancies=bool(discrepancies),
    )

    return ReconciliationResult(
        user_id=user_id,
        account_id=account_id,
        source_state=source_state,
        state=state,
        observed_at=observed_at,
        discrepancies=discrepancies,
    )
