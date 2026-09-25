from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from apps.core.application.shadow_parity import (
    ALL_SHADOW_PARITY_DIMENSIONS,
    ShadowEvidenceState,
)
from scripts.phase14_reference_evidence import observe_reference_once
from scripts.phase14_reference_evidence_writer import write_reference_evidence


def _dimensions():
    return {
        dimension.value: {"normalized": dimension.value}
        for dimension in ALL_SHADOW_PARITY_DIMENSIONS
    }


def test_writer_round_trip_produces_current_complete_reference(tmp_path, monkeypatch) -> None:
    path = tmp_path / "reference.json"
    write_reference_evidence(
        output_path=path,
        source="legacy-runtime",
        dimensions=_dimensions(),
        observed_at=datetime.now(UTC),
    )

    monkeypatch.setenv("NEXUS_PHASE14_REFERENCE_EVIDENCE_FILE", str(path))
    monkeypatch.setenv("NEXUS_PHASE14_REFERENCE_MAX_AGE_SECONDS", "300")
    evidence = asyncio.run(observe_reference_once())

    assert evidence.state is ShadowEvidenceState.CURRENT
    assert evidence.source == "legacy-runtime"
    assert len(evidence.dimensions) == 8


def test_writer_rejects_missing_dimension(tmp_path) -> None:
    dimensions = _dimensions()
    dimensions.pop("execution_quality")

    with pytest.raises(ValueError, match="dimensions must be exact"):
        write_reference_evidence(
            output_path=tmp_path / "reference.json",
            source="legacy-runtime",
            dimensions=dimensions,
        )
