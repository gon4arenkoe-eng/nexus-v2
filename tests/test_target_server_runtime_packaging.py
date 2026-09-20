from __future__ import annotations

from pathlib import Path

COMPOSE = Path("infra/deploy/compose.production.yml")
DOCKERFILE = Path("infra/containers/Dockerfile.release")
RUNTIME = Path("scripts/target_server_runtime.py")


def test_release_image_contains_target_server_runtime_source() -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    assert "COPY scripts ./scripts" in dockerfile
    assert RUNTIME.exists()


def test_production_compose_has_long_running_core_runtime() -> None:
    compose = COMPOSE.read_text(encoding="utf-8")

    assert "nexus-core:" in compose
    assert "scripts.target_server_runtime" in compose
    assert "restart: unless-stopped" in compose
    assert "127.0.0.1:${NEXUS_CORE_PORT:-8080}:8080" in compose
    assert "/health" in compose


def test_release_validation_service_is_preserved() -> None:
    compose = COMPOSE.read_text(encoding="utf-8")

    assert "nexus-release-verify:" in compose
    assert "release-validation" in compose
    assert "production-release-validation" in compose


def test_core_runtime_remains_hardened_and_read_only() -> None:
    compose = COMPOSE.read_text(encoding="utf-8")

    core = compose.split("nexus-core:", 1)[1].split(
        "nexus-release-verify:",
        1,
    )[0]

    assert "read_only: true" in core
    assert "no-new-privileges:true" in core
    assert "cap_drop:" in core
    assert "- ALL" in core
    assert "DATABASE_URL" not in core
    assert "REDIS_URL" not in core
    assert "SECRET" not in core
    assert "API_KEY" not in core
