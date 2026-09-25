from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime

from apps.core.application.shadow_parity import (
    ALL_SHADOW_PARITY_DIMENSIONS,
    ShadowBehaviorEvidence,
    ShadowEvidenceState,
    ShadowParityDimension,
)
from scripts.bingx_vst_observer_runtime import ObserverSnapshot
from scripts.phase14_bingx_shadow_runtime import (
    _payload,
    run_shadow_cycle,
)


def _observer_snapshot() -> ObserverSnapshot:
    return ObserverSnapshot(
        environment="BINGX_VST",
        symbol="BTCUSDT",
        observed_at="2026-09-21T14:00:00+00:00",
        source_state="CURRENT",
        account_query="PASS",
        open_orders_query="PASS",
        positions_query="PASS",
        fills_query="PASS",
        balance_assets=("VST",),
        open_order_count=0,
        position_count=0,
        fill_count=0,
        writes_attempted=False,
        production_authority=False,
        strategy_execution_allowed=False,
    )


async def _observer_current() -> ObserverSnapshot:
    return _observer_snapshot()


async def _candidate_ok() -> dict[str, object]:
    return {
        "service": "nexus-v2-core",
        "mode": "SIMULATION_ONLY",
        "startup_reconciliation": "MATCHED",
        "strategy_execution_allowed": True,
        "portfolio_risk": "APPROVED",
        "execution_state": "COMPLETED",
        "order_status": "ACCEPTED",
        "post_execution_reconciliation": "MATCHED",
        "venue_writes": 1,
        "real_exchange_writes": 0,
        "production_authority": False,
        "status": "RUNNING",
        "shadow_evidence": {
            "signals_intents": {"intent": "same"},
            "risk_decisions": {"risk": "same"},
            "order_intent": {"order": "same"},
            "positions": {"positions": "same"},
            "fills_reconciliation": {"fills": "same"},
            "pnl_attribution": {"pnl": "same"},
            "execution_quality": {"quality": "same"},
            "failures_stale_states": {"failure": "same"},
        },
    }


async def _reference_ok() -> ShadowBehaviorEvidence:
    candidate = await _candidate_ok()
    raw = candidate["shadow_evidence"]
    assert isinstance(raw, dict)
    return ShadowBehaviorEvidence(
        source="LEGACY_REFERENCE",
        observed_at=datetime.now(UTC),
        state=ShadowEvidenceState.CURRENT,
        dimensions={
            dimension: raw[dimension.value]
            for dimension in ALL_SHADOW_PARITY_DIMENSIONS
        },
    )


def test_shadow_cycle_combines_real_readonly_and_simulated_candidate() -> None:
    snapshot = asyncio.run(
        run_shadow_cycle(
            observer=_observer_current,
            candidate_runner=_candidate_ok,
            reference_runner=_reference_ok,
        )
    )

    assert snapshot.ready is True
    assert snapshot.environment == "BINGX_VST"
    assert snapshot.source_state == "CURRENT"

    assert snapshot.simulated_venue_writes == 1
    assert snapshot.real_exchange_writes == 0

    assert snapshot.production_authority is False
    assert snapshot.strategy_execution_allowed is False
    assert snapshot.writes_attempted is False

    # Foundation readiness must never claim full shadow parity closure.
    assert snapshot.shadow_gate_open is False
    assert snapshot.parity_state == "PASS"
    assert set(snapshot.parity_dimensions.values()) == {"PASS"}
    assert snapshot.parity_critical_mismatches == ()
    assert snapshot.error is None


def test_shadow_cycle_fails_closed_when_real_observation_is_unavailable() -> None:
    async def unavailable() -> ObserverSnapshot:
        return replace(
            _observer_snapshot(),
            source_state="UNAVAILABLE",
        )

    snapshot = asyncio.run(
        run_shadow_cycle(
            observer=unavailable,
            candidate_runner=_candidate_ok,
            reference_runner=_reference_ok,
        )
    )

    assert snapshot.ready is False
    assert snapshot.shadow_gate_open is False
    assert (
        snapshot.error
        == "bingx_observation_not_current_or_not_read_only"
    )


def test_shadow_cycle_fails_closed_if_candidate_reports_real_exchange_write() -> None:
    async def unsafe_candidate() -> dict[str, object]:
        candidate = await _candidate_ok()
        candidate["real_exchange_writes"] = 1
        return candidate

    snapshot = asyncio.run(
        run_shadow_cycle(
            observer=_observer_current,
            candidate_runner=unsafe_candidate,
            reference_runner=_reference_ok,
        )
    )

    assert snapshot.ready is False
    assert snapshot.real_exchange_writes == 1
    assert snapshot.shadow_gate_open is False
    assert (
        snapshot.error
        == "candidate_real_exchange_write_detected"
    )


def test_runtime_payload_never_exposes_live_authority() -> None:
    snapshot = asyncio.run(
        run_shadow_cycle(
            observer=_observer_current,
            candidate_runner=_candidate_ok,
            reference_runner=_reference_ok,
        )
    )

    payload = _payload(snapshot)

    assert payload["runtime_mode"] == (
        "PHASE14_BINGX_VST_SHADOW_READ_ONLY"
    )
    assert payload["ready"] is True
    assert payload["production_authority"] is False
    assert payload["strategy_execution_allowed"] is False
    assert payload["writes_attempted"] is False
    assert payload["shadow_gate_open"] is False


def test_shadow_cycle_fails_closed_on_reference_mismatch() -> None:
    async def mismatched_reference() -> ShadowBehaviorEvidence:
        reference = await _reference_ok()
        dimensions = dict(reference.dimensions)
        dimensions[ShadowParityDimension.ORDER_INTENT] = {"order": "different"}
        return ShadowBehaviorEvidence(
            source=reference.source,
            observed_at=reference.observed_at,
            state=reference.state,
            dimensions=dimensions,
        )

    snapshot = asyncio.run(
        run_shadow_cycle(
            observer=_observer_current,
            candidate_runner=_candidate_ok,
            reference_runner=mismatched_reference,
        )
    )
    assert snapshot.ready is False
    assert snapshot.parity_state == "FAIL"
    assert snapshot.parity_critical_mismatches == ("order_intent",)
    assert snapshot.error == "shadow_parity_mismatch"


def test_shadow_cycle_missing_reference_is_not_comparable() -> None:
    async def unavailable_reference() -> ShadowBehaviorEvidence:
        return ShadowBehaviorEvidence(
            source="LEGACY_REFERENCE",
            observed_at=datetime.now(UTC),
            state=ShadowEvidenceState.UNAVAILABLE,
            dimensions={
                dimension: None
                for dimension in ALL_SHADOW_PARITY_DIMENSIONS
            },
            errors=("reference unavailable",),
        )

    snapshot = asyncio.run(
        run_shadow_cycle(
            observer=_observer_current,
            candidate_runner=_candidate_ok,
            reference_runner=unavailable_reference,
        )
    )
    assert snapshot.ready is False
    assert snapshot.parity_state == "NOT_COMPARABLE"
    assert set(snapshot.parity_dimensions.values()) == {"NOT_COMPARABLE"}
    assert snapshot.error == "shadow_parity_not_comparable"


def test_candidate_without_full_shadow_evidence_is_not_comparable() -> None:
    async def incomplete_candidate() -> dict[str, object]:
        candidate = await _candidate_ok()
        raw = candidate["shadow_evidence"]
        assert isinstance(raw, dict)
        raw.pop("pnl_attribution")
        return candidate

    snapshot = asyncio.run(
        run_shadow_cycle(
            observer=_observer_current,
            candidate_runner=incomplete_candidate,
            reference_runner=_reference_ok,
        )
    )

    assert snapshot.ready is False
    assert snapshot.parity_state == "NOT_COMPARABLE"
    assert snapshot.error == "shadow_parity_not_comparable"
