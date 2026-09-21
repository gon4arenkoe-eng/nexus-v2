"""Deterministic Phase 14 shadow-parity evidence comparison.

This module compares behavior evidence only. It owns no venue writes, execution
permission, strategy activation or production authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping, TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


class ShadowEvidenceState(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class ShadowParityState(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_COMPARABLE = "NOT_COMPARABLE"


class ShadowParityDimension(StrEnum):
    SIGNALS_INTENTS = "signals_intents"
    RISK_DECISIONS = "risk_decisions"
    ORDER_INTENT = "order_intent"
    POSITIONS = "positions"
    FILLS_RECONCILIATION = "fills_reconciliation"
    PNL_ATTRIBUTION = "pnl_attribution"
    EXECUTION_QUALITY = "execution_quality"
    FAILURES_STALE_STATES = "failures_stale_states"


ALL_SHADOW_PARITY_DIMENSIONS: tuple[ShadowParityDimension, ...] = tuple(
    ShadowParityDimension
)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("shadow evidence timestamp must be timezone-aware")
    return value.astimezone(UTC)


def _canonical_json(value: JsonValue) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _fingerprint(value: JsonValue) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _frozen_dimensions(
    dimensions: Mapping[ShadowParityDimension, JsonValue],
) -> Mapping[ShadowParityDimension, JsonValue]:
    missing = set(ALL_SHADOW_PARITY_DIMENSIONS) - set(dimensions)
    extra = set(dimensions) - set(ALL_SHADOW_PARITY_DIMENSIONS)
    if missing or extra:
        raise ValueError(
            "shadow evidence dimensions must be exact; "
            f"missing={sorted(item.value for item in missing)} "
            f"extra={sorted(str(item) for item in extra)}"
        )
    return MappingProxyType(dict(dimensions))


@dataclass(frozen=True, slots=True)
class ShadowBehaviorEvidence:
    source: str
    observed_at: datetime
    state: ShadowEvidenceState
    dimensions: Mapping[ShadowParityDimension, JsonValue]
    errors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        source = self.source.strip()
        if not source:
            raise ValueError("shadow evidence source must be non-empty")
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "observed_at", _utc(self.observed_at))
        if not isinstance(self.state, ShadowEvidenceState):
            raise ValueError("state must be ShadowEvidenceState")
        object.__setattr__(self, "dimensions", _frozen_dimensions(self.dimensions))
        object.__setattr__(
            self,
            "errors",
            tuple(item.strip() for item in self.errors if item.strip()),
        )


@dataclass(frozen=True, slots=True)
class ShadowDimensionComparison:
    dimension: ShadowParityDimension
    state: ShadowParityState
    reference_fingerprint: str | None
    candidate_fingerprint: str | None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ShadowParityReport:
    state: ShadowParityState
    comparisons: tuple[ShadowDimensionComparison, ...]
    critical_mismatches: tuple[str, ...]
    reference_source: str
    candidate_source: str

    @property
    def dimension_states(self) -> Mapping[str, str]:
        return MappingProxyType(
            {item.dimension.value: item.state.value for item in self.comparisons}
        )


def compare_shadow_behavior(
    reference: ShadowBehaviorEvidence,
    candidate: ShadowBehaviorEvidence,
) -> ShadowParityReport:
    source_comparable = (
        reference.state is ShadowEvidenceState.CURRENT
        and candidate.state is ShadowEvidenceState.CURRENT
    )

    comparisons: list[ShadowDimensionComparison] = []
    for dimension in ALL_SHADOW_PARITY_DIMENSIONS:
        left = reference.dimensions[dimension]
        right = candidate.dimensions[dimension]

        if not source_comparable:
            comparisons.append(
                ShadowDimensionComparison(
                    dimension=dimension,
                    state=ShadowParityState.NOT_COMPARABLE,
                    reference_fingerprint=None,
                    candidate_fingerprint=None,
                    reason=(
                        "non-current evidence: "
                        f"reference={reference.state.value}, "
                        f"candidate={candidate.state.value}"
                    ),
                )
            )
            continue

        if left is None or right is None:
            comparisons.append(
                ShadowDimensionComparison(
                    dimension=dimension,
                    state=ShadowParityState.NOT_COMPARABLE,
                    reference_fingerprint=(None if left is None else _fingerprint(left)),
                    candidate_fingerprint=(None if right is None else _fingerprint(right)),
                    reason="dimension evidence unavailable",
                )
            )
            continue

        left_hash = _fingerprint(left)
        right_hash = _fingerprint(right)
        state = (
            ShadowParityState.PASS
            if left_hash == right_hash
            else ShadowParityState.FAIL
        )
        comparisons.append(
            ShadowDimensionComparison(
                dimension=dimension,
                state=state,
                reference_fingerprint=left_hash,
                candidate_fingerprint=right_hash,
                reason=None if state is ShadowParityState.PASS else "evidence mismatch",
            )
        )

    if any(item.state is ShadowParityState.FAIL for item in comparisons):
        overall = ShadowParityState.FAIL
    elif any(item.state is ShadowParityState.NOT_COMPARABLE for item in comparisons):
        overall = ShadowParityState.NOT_COMPARABLE
    else:
        overall = ShadowParityState.PASS

    critical = tuple(
        item.dimension.value
        for item in comparisons
        if item.state is ShadowParityState.FAIL
    )

    return ShadowParityReport(
        state=overall,
        comparisons=tuple(comparisons),
        critical_mismatches=critical,
        reference_source=reference.source,
        candidate_source=candidate.source,
    )
