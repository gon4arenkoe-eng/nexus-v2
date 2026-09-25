"""Read a bounded, explicit legacy/reference Phase 14 evidence snapshot.

The adapter is read-only and fail-closed. It never reaches an exchange and it
never invents legacy/reference values when the producer is absent or stale.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from apps.core.application.shadow_parity import (
    ALL_SHADOW_PARITY_DIMENSIONS,
    ShadowBehaviorEvidence,
    ShadowEvidenceState,
    ShadowParityDimension,
)

DEFAULT_MAX_AGE_SECONDS: Final = 120.0


def _empty_dimensions() -> dict[ShadowParityDimension, None]:
    return {dimension: None for dimension in ALL_SHADOW_PARITY_DIMENSIONS}


def _unavailable(reason: str) -> ShadowBehaviorEvidence:
    return ShadowBehaviorEvidence(
        source="LEGACY_REFERENCE",
        observed_at=datetime.now(UTC),
        state=ShadowEvidenceState.UNAVAILABLE,
        dimensions=_empty_dimensions(),
        errors=(reason,),
    )


def _parse_observed_at(raw: object) -> datetime:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("reference observed_at must be ISO-8601 text")
    value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("reference observed_at must be timezone-aware")
    return value.astimezone(UTC)


def _max_age_seconds() -> float:
    raw = os.environ.get(
        "NEXUS_PHASE14_REFERENCE_MAX_AGE_SECONDS",
        str(DEFAULT_MAX_AGE_SECONDS),
    )
    value = float(raw)
    if value <= 0:
        raise ValueError("NEXUS_PHASE14_REFERENCE_MAX_AGE_SECONDS must be > 0")
    return value


def _load_reference_sync() -> ShadowBehaviorEvidence:
    raw_path = os.environ.get("NEXUS_PHASE14_REFERENCE_EVIDENCE_FILE", "").strip()
    if not raw_path:
        return _unavailable("reference evidence file is not configured")

    path = Path(raw_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _unavailable(f"reference evidence read failed: {type(exc).__name__}: {exc}")

    try:
        observed_at = _parse_observed_at(payload.get("observed_at"))
        source = str(payload.get("source", "LEGACY_REFERENCE")).strip()
        source_state = ShadowEvidenceState(str(payload.get("source_state", "UNKNOWN")))
        raw_dimensions = payload.get("dimensions")
        if not isinstance(raw_dimensions, dict):
            raise ValueError("reference dimensions must be an object")

        dimensions = {
            dimension: raw_dimensions.get(dimension.value)
            for dimension in ALL_SHADOW_PARITY_DIMENSIONS
        }

        missing = tuple(
            dimension.value
            for dimension, value in dimensions.items()
            if value is None
        )
        invalid = tuple(
            dimension.value
            for dimension, value in dimensions.items()
            if value is not None and not isinstance(value, dict)
        )

        errors_raw = payload.get("errors", [])
        if not isinstance(errors_raw, list):
            raise ValueError("reference errors must be a list")
        errors = tuple(str(item) for item in errors_raw)

        if missing or invalid:
            source_state = ShadowEvidenceState.DEGRADED
            details: list[str] = []
            if missing:
                details.append("missing=" + ",".join(missing))
            if invalid:
                details.append("invalid=" + ",".join(invalid))
            errors = (*errors, "reference evidence incomplete: " + " ".join(details))

        age = (datetime.now(UTC) - observed_at).total_seconds()
        if age < 0:
            raise ValueError("reference evidence timestamp is in the future")
        if age > _max_age_seconds():
            source_state = ShadowEvidenceState.STALE
            errors = (*errors, f"reference evidence stale: age_seconds={age:.3f}")

        return ShadowBehaviorEvidence(
            source=source,
            observed_at=observed_at,
            state=source_state,
            dimensions=dimensions,
            errors=errors,
        )
    except (TypeError, ValueError) as exc:
        return _unavailable(f"reference evidence invalid: {exc}")


async def observe_reference_once() -> ShadowBehaviorEvidence:
    return await asyncio.to_thread(_load_reference_sync)
