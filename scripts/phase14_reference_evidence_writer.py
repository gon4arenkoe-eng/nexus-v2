"""Validate and atomically publish normalized Phase 14 reference evidence.

This is a read-side bridge for an external legacy/reference runtime. It does
not execute strategies, access exchanges or synthesize reference behavior.
The caller must provide factual normalized evidence for all eight dimensions.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping

from apps.core.application.shadow_parity import ALL_SHADOW_PARITY_DIMENSIONS


def _normalized_dimensions(raw: Mapping[str, object]) -> dict[str, object]:
    expected = {item.value for item in ALL_SHADOW_PARITY_DIMENSIONS}
    actual = set(raw)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(
            "reference dimensions must be exact; "
            f"missing={missing} extra={extra}"
        )

    normalized: dict[str, object] = {}
    for name in sorted(expected):
        value = raw[name]
        if not isinstance(value, dict):
            raise ValueError(
                f"reference dimension {name} must be an object"
            )
        normalized[name] = value
    return normalized


def write_reference_evidence(
    *,
    output_path: Path,
    source: str,
    dimensions: Mapping[str, object],
    observed_at: datetime | None = None,
    errors: tuple[str, ...] = (),
) -> None:
    source = source.strip()
    if not source:
        raise ValueError("reference source must be non-empty")

    timestamp = observed_at or datetime.now(UTC)
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("reference observed_at must be timezone-aware")

    payload = {
        "source": source,
        "observed_at": timestamp.astimezone(UTC).isoformat(),
        "source_state": "CURRENT",
        "dimensions": _normalized_dimensions(dimensions),
        "errors": [item.strip() for item in errors if item.strip()],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(output_path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    os.replace(temporary, output_path)


def main() -> int:
    raw_path = os.environ.get(
        "NEXUS_PHASE14_REFERENCE_EVIDENCE_FILE",
        "",
    ).strip()
    if not raw_path:
        raise RuntimeError(
            "NEXUS_PHASE14_REFERENCE_EVIDENCE_FILE is required"
        )

    payload = json.load(sys.stdin)
    if not isinstance(payload, dict):
        raise ValueError("reference producer input must be an object")

    source = str(payload.get("source", "LEGACY_REFERENCE"))
    dimensions = payload.get("dimensions")
    if not isinstance(dimensions, dict):
        raise ValueError("reference producer dimensions must be an object")

    errors_raw = payload.get("errors", [])
    if not isinstance(errors_raw, list):
        raise ValueError("reference producer errors must be a list")

    write_reference_evidence(
        output_path=Path(raw_path),
        source=source,
        dimensions=dimensions,
        errors=tuple(str(item) for item in errors_raw),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
