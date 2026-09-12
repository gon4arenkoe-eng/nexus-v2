from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.validate_deploy_ref import validate_image_ref

ROOT = Path(__file__).resolve().parents[1]


def _digest(char: str = "a") -> str:
    return f"sha256:{char * 64}"


def test_accepts_expected_ghcr_digest_reference() -> None:
    ref = f"ghcr.io/gon4arenkoe-eng/nexus-v2@{_digest()}"
    assert validate_image_ref(
        ref,
        repository="gon4arenkoe-eng/nexus-v2",
    ) == ref


@pytest.mark.parametrize(
    "ref",
    (
        "ghcr.io/gon4arenkoe-eng/nexus-v2:latest",
        "ghcr.io/gon4arenkoe-eng/nexus-v2:v1.0.0",
        "ghcr.io/gon4arenkoe-eng/nexus-v2@sha256:abc",
        f"docker.io/gon4arenkoe-eng/nexus-v2@{_digest()}",
        f"ghcr.io/other/nexus-v2@{_digest()}",
    ),
)
def test_rejects_mutable_or_wrong_repository_references(ref: str) -> None:
    with pytest.raises(ValueError):
        validate_image_ref(ref, repository="gon4arenkoe-eng/nexus-v2")


def test_production_compose_has_no_build_authority() -> None:
    text = (ROOT / "infra/deploy/compose.production.yml").read_text(
        encoding="utf-8"
    )
    assert "build:" not in text.lower()
    assert ":latest" not in text.lower()
    assert "${NEXUS_IMAGE_REF:?" in text
    assert "release-validation" in text
    assert "pull_policy: always" in text


def test_release_evidence_schema_binds_required_evidence() -> None:
    schema = json.loads(
        (ROOT / "infra/deploy/release-evidence.schema.json").read_text(
            encoding="utf-8"
        )
    )
    required = set(schema["required"])
    assert {
        "source_commit",
        "image_ref",
        "image_digest",
        "alembic_head",
        "sbom_attested",
        "provenance_attested",
        "backup_reference",
        "backup_sha256",
        "authorization_state",
    }.issubset(required)


def test_rollback_runbook_requires_previous_verified_digest() -> None:
    text = (ROOT / "docs/runbooks/digest-deploy-rollback.md").read_text(
        encoding="utf-8"
    )
    assert "previous verified digest" in text
    assert "image@sha256" in text
    assert "NO BUILD ON PRODUCTION" in text
    assert "Phase 16" in text
    assert "reconciliation" in text


def test_backup_runbook_keeps_phase15_drill_explicit() -> None:
    text = (ROOT / "docs/runbooks/backup-restore-foundation.md").read_text(
        encoding="utf-8"
    )
    assert "pg_dump" in text
    assert "pg_restore" in text
    assert "SHA-256" in text
    assert "isolated restore rehearsal" in text
    assert "Phase 15" in text
    assert "production restore" in text


def test_validator_has_no_remote_deploy_authority() -> None:
    text = (ROOT / "scripts/validate_deploy_ref.py").read_text(
        encoding="utf-8"
    ).lower()
    assert "paramiko" not in text
    assert "fabric" not in text
    assert "scp " not in text
    assert "ssh " not in text
    assert "docker build" not in text
