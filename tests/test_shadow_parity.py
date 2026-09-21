from __future__ import annotations

from datetime import UTC, datetime

from apps.core.application.shadow_parity import (
    ALL_SHADOW_PARITY_DIMENSIONS,
    ShadowBehaviorEvidence,
    ShadowEvidenceState,
    ShadowParityDimension,
    ShadowParityState,
    compare_shadow_behavior,
)

NOW = datetime(2026, 9, 21, 18, 0, tzinfo=UTC)


def _dimensions(value: object = "same"):
    return {dimension: {"value": value} for dimension in ALL_SHADOW_PARITY_DIMENSIONS}


def _evidence(*, state=ShadowEvidenceState.CURRENT, dimensions=None):
    return ShadowBehaviorEvidence(
        source="source",
        observed_at=NOW,
        state=state,
        dimensions=_dimensions() if dimensions is None else dimensions,
    )


def test_all_phase14_dimensions_are_explicit_and_stable() -> None:
    assert tuple(item.value for item in ALL_SHADOW_PARITY_DIMENSIONS) == (
        "signals_intents",
        "risk_decisions",
        "order_intent",
        "positions",
        "fills_reconciliation",
        "pnl_attribution",
        "execution_quality",
        "failures_stale_states",
    )


def test_identical_current_evidence_passes_all_dimensions() -> None:
    report = compare_shadow_behavior(_evidence(), _evidence())
    assert report.state is ShadowParityState.PASS
    assert report.critical_mismatches == ()
    assert set(report.dimension_states.values()) == {"PASS"}


def test_each_dimension_mismatch_is_fail_and_named() -> None:
    for dimension in ALL_SHADOW_PARITY_DIMENSIONS:
        changed = _dimensions()
        changed[dimension] = {"value": "different"}
        report = compare_shadow_behavior(_evidence(), _evidence(dimensions=changed))
        assert report.state is ShadowParityState.FAIL
        assert report.critical_mismatches == (dimension.value,)
        assert report.dimension_states[dimension.value] == "FAIL"


def test_missing_dimension_payload_is_not_comparable_not_pass() -> None:
    changed = _dimensions()
    changed[ShadowParityDimension.PNL_ATTRIBUTION] = None
    report = compare_shadow_behavior(_evidence(), _evidence(dimensions=changed))
    assert report.state is ShadowParityState.NOT_COMPARABLE
    assert report.dimension_states["pnl_attribution"] == "NOT_COMPARABLE"


def test_stale_reference_fails_closed_as_not_comparable() -> None:
    report = compare_shadow_behavior(
        _evidence(state=ShadowEvidenceState.STALE),
        _evidence(),
    )
    assert report.state is ShadowParityState.NOT_COMPARABLE
    assert set(report.dimension_states.values()) == {"NOT_COMPARABLE"}


def test_dimensions_must_be_exact() -> None:
    dimensions = _dimensions()
    dimensions.pop(ShadowParityDimension.EXECUTION_QUALITY)
    try:
        _evidence(dimensions=dimensions)
    except ValueError as exc:
        assert "dimensions must be exact" in str(exc)
    else:
        raise AssertionError("missing parity dimension was accepted")
