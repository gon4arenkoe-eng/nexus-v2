from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release-image.yml"
CHECK = ROOT / "infra" / "github" / "supply_chain_evidence_check.py"


def _workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_release_workflow_emits_sbom_attestation() -> None:
    assert "sbom: true" in _workflow()


def test_release_workflow_emits_max_provenance() -> None:
    assert "provenance: mode=max" in _workflow()


def test_attestations_are_bound_to_registry_push() -> None:
    text = _workflow()
    assert "docker/build-push-action@" in text
    assert "push: true" in text


def test_supply_chain_policy_checker_exists() -> None:
    assert CHECK.is_file()


def test_supply_chain_slice_has_no_production_remote_authority() -> None:
    text = _workflow().lower()
    forbidden = ("appleboy/ssh-action", "scp-action", "ssh-action")
    assert all(token not in text for token in forbidden)
