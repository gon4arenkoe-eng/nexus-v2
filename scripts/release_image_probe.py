"""Fail-closed smoke probe for the Phase 12 release artifact.

This is intentionally not a production service entry point. Phase 12 first
establishes immutable CI-built packaging. Deployment/runtime wiring is a
separate verified slice.
"""

from __future__ import annotations

import importlib
import json
import os

REQUIRED_MODULES = (
    "apps.core.application.control_plane",
    "apps.core.application.portfolio_risk",
    "apps.intelligence.application.market_context",
    "apps.aiea.application.research_loop",
    "packages.contracts.control_plane",
)


def main() -> int:
    for module_name in REQUIRED_MODULES:
        importlib.import_module(module_name)

    evidence = {
        "artifact": "nexus-v2",
        "runtime_mode": os.environ.get("NEXUS_RUNTIME_MODE", "unknown"),
        "status": "READY_ARTIFACT",
    }
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
