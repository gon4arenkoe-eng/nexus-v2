"""Static fail-closed policy checks for Phase 12 release foundation."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "release-image.yml"
DOCKERFILE = ROOT / "infra" / "containers" / "Dockerfile.release"
PROBE = ROOT / "scripts" / "release_image_probe.py"


def _require(text: str, *needles: str) -> None:
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"missing required release controls: {missing}")


def _forbid(text: str, *needles: str) -> None:
    found = [needle for needle in needles if needle in text]
    if found:
        raise SystemExit(f"forbidden release authority/control found: {found}")


def main() -> int:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    probe = PROBE.read_text(encoding="utf-8")

    _require(
        workflow,
        "ghcr.io",
        "packages: write",
        "docker/build-push-action@f2a1d5e99d037542a71f64918e516c093c6f3fc4",
        "push: true",
        "NEXUS_COMMIT_SHA=${{ github.sha }}",
        "steps.build.outputs.digest",
        "needs: verify",
    )
    _forbid(
        workflow.lower(),
        "ssh ",
        "scp ",
        "docker compose up",
        "docker-compose up",
        "nexus-bot",
    )

    _require(
        dockerfile,
        "FROM python:3.13-slim@sha256:",
        "USER nexus:nexus",
        'ENTRYPOINT ["python", "-m", "scripts.release_image_probe"]',
    )
    _forbid(dockerfile, "COPY . .", "ENV BINANCE", "ENV BYBIT", "ENV BINGX")
    _require(probe, '"status": "READY_ARTIFACT"')

    print("RELEASE_PIPELINE_FOUNDATION_POLICY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
