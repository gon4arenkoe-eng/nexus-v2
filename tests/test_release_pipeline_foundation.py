from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release-image.yml"
DOCKERFILE = ROOT / "infra" / "containers" / "Dockerfile.release"
DOCKERIGNORE = ROOT / ".dockerignore"
POLICY = ROOT / "infra" / "github" / "release_pipeline_check.py"
PROBE = ROOT / "scripts" / "release_image_probe.py"


def test_release_foundation_files_exist() -> None:
    for path in (WORKFLOW, DOCKERFILE, DOCKERIGNORE, POLICY, PROBE):
        assert path.is_file(), path


def test_release_workflow_verifies_before_publish() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "needs: verify" in text
    assert "packages: write" in text
    assert (
        "docker/build-push-action@"
        "f2a1d5e99d037542a71f64918e516c093c6f3fc4"
    ) in text
    assert "push: true" in text
    assert "steps.build.outputs.digest" in text
    assert "NEXUS_COMMIT_SHA=${{ github.sha }}" in text


def test_release_workflow_has_no_production_deploy_authority() -> None:
    text = WORKFLOW.read_text(encoding="utf-8").lower()

    forbidden = (
        "ssh ",
        "scp ",
        "docker compose up",
        "docker-compose up",
        "nexus-bot",
    )
    for marker in forbidden:
        assert marker not in text


def test_release_image_is_non_root_and_base_is_digest_pinned() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8")

    assert "FROM python:3.13-slim@sha256:" in text
    assert "USER nexus:nexus" in text
    assert "COPY . ." not in text


def test_docker_context_excludes_secrets_and_local_state() -> None:
    text = DOCKERIGNORE.read_text(encoding="utf-8")

    for marker in (".git", ".venv", ".env", ".nexus-backups", "*.dump"):
        assert marker in text


def test_release_policy_script_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(POLICY)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "RELEASE_PIPELINE_FOUNDATION_POLICY=PASS" in result.stdout


def test_release_image_probe_imports_canonical_components() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "scripts.release_image_probe"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert '"status": "READY_ARTIFACT"' in result.stdout
