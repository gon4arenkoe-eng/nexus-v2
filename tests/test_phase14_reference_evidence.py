from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime

from apps.core.application.shadow_parity import ShadowEvidenceState
from scripts.phase14_reference_evidence import observe_reference_once


def _payload(observed_at: str):
    names = (
        "signals_intents",
        "risk_decisions",
        "order_intent",
        "positions",
        "fills_reconciliation",
        "pnl_attribution",
        "execution_quality",
        "failures_stale_states",
    )
    return {
        "source": "legacy-runtime",
        "observed_at": observed_at,
        "source_state": "CURRENT",
        "dimensions": {name: {"fingerprint_material": name} for name in names},
        "errors": [],
    }


def test_missing_reference_source_is_explicit_unavailable(monkeypatch) -> None:
    monkeypatch.delenv("NEXUS_PHASE14_REFERENCE_EVIDENCE_FILE", raising=False)
    evidence = asyncio.run(observe_reference_once())
    assert evidence.state is ShadowEvidenceState.UNAVAILABLE
    assert evidence.errors


def test_reference_source_reads_all_dimensions(tmp_path, monkeypatch) -> None:
    path = tmp_path / "reference.json"
    path.write_text(
        json.dumps(_payload(datetime.now(UTC).isoformat())),
        encoding="utf-8",
    )
    monkeypatch.setenv("NEXUS_PHASE14_REFERENCE_EVIDENCE_FILE", str(path))
    monkeypatch.setenv("NEXUS_PHASE14_REFERENCE_MAX_AGE_SECONDS", "300")
    evidence = asyncio.run(observe_reference_once())
    assert evidence.state is ShadowEvidenceState.CURRENT
    assert len(evidence.dimensions) == 8


def test_stale_reference_source_is_marked_stale(tmp_path, monkeypatch) -> None:
    path = tmp_path / "reference.json"
    path.write_text(
        json.dumps(_payload("2026-01-01T00:00:00+00:00")),
        encoding="utf-8",
    )
    monkeypatch.setenv("NEXUS_PHASE14_REFERENCE_EVIDENCE_FILE", str(path))
    monkeypatch.setenv("NEXUS_PHASE14_REFERENCE_MAX_AGE_SECONDS", "1")
    evidence = asyncio.run(observe_reference_once())
    assert evidence.state is ShadowEvidenceState.STALE
    assert evidence.errors
