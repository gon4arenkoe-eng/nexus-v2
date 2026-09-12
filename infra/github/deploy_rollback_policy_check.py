"""Fail-closed static policy for Phase 12 deploy/rollback foundation."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "infra" / "deploy" / "compose.production.yml"
SCHEMA = ROOT / "infra" / "deploy" / "release-evidence.schema.json"
ROLLBACK = ROOT / "docs" / "runbooks" / "digest-deploy-rollback.md"
BACKUP = ROOT / "docs" / "runbooks" / "backup-restore-foundation.md"
VALIDATOR = ROOT / "scripts" / "validate_deploy_ref.py"


def _require(text: str, marker: str, *, source: str) -> None:
    if marker not in text:
        raise RuntimeError(f"{source} missing required marker: {marker}")


def main() -> int:
    for path in (COMPOSE, SCHEMA, ROLLBACK, BACKUP, VALIDATOR):
        if not path.is_file():
            raise RuntimeError(f"required release file missing: {path}")

    compose = COMPOSE.read_text(encoding="utf-8")
    lowered = compose.lower()
    if "build:" in lowered:
        raise RuntimeError(
            "production release manifest must not contain build:"
        )
    if ":latest" in lowered:
        raise RuntimeError("production release manifest must not use latest")
    _require(compose, "${NEXUS_IMAGE_REF:?", source="compose.production.yml")
    _require(compose, "pull_policy: always", source="compose.production.yml")
    _require(compose, "release-validation", source="compose.production.yml")
    _require(
        compose,
        "no-new-privileges:true",
        source="compose.production.yml",
    )
    _require(compose, "cap_drop:", source="compose.production.yml")

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    required = set(schema.get("required", []))
    expected = {
        "source_commit",
        "image_ref",
        "image_digest",
        "alembic_head",
        "sbom_attested",
        "provenance_attested",
        "backup_reference",
        "backup_sha256",
        "recorded_at",
        "authorization_state",
    }
    if not expected.issubset(required):
        raise RuntimeError(
            "release evidence schema is missing required fields"
        )

    rollback = ROLLBACK.read_text(encoding="utf-8")
    for marker in (
        "previous verified digest",
        "image@sha256",
        "NO BUILD ON PRODUCTION",
        "Phase 16",
        "reconciliation",
    ):
        _require(rollback, marker, source="digest-deploy-rollback.md")

    backup = BACKUP.read_text(encoding="utf-8")
    for marker in (
        "pg_dump",
        "SHA-256",
        "isolated restore rehearsal",
        "Phase 15",
        "production restore",
    ):
        _require(backup, marker, source="backup-restore-foundation.md")

    validator = VALIDATOR.read_text(encoding="utf-8").lower()
    for forbidden in ("paramiko", "fabric", "scp ", "ssh ", "docker build"):
        if forbidden in validator:
            raise RuntimeError(
                "validator contains deployment authority: "
                f"{forbidden}"
            )

    print("DIGEST_DEPLOY_ROLLBACK_POLICY=PASS")
    print("DEPLOY_REFERENCE=DIGEST_ONLY")
    print("ROLLBACK_REFERENCE=PREVIOUS_VERIFIED_DIGEST")
    print("BACKUP_BEFORE_CUTOVER=REQUIRED")
    print("PRODUCTION_DEPLOY_AUTHORITY=NO")
    print("NO_BUILD_ON_PRODUCTION=PRESERVED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
