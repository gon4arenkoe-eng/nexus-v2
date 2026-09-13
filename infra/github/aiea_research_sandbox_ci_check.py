"""Fail-closed static policy check for AIEA sandbox runtime-certification CI."""
from __future__ import annotations

from pathlib import Path
import re

WORKFLOW = Path(".github/workflows/aiea-research-sandbox-certification.yml")
_DIGEST_RE = re.compile(r"python@sha256:[0-9a-f]{64}")


def validate_workflow_text(text: str) -> tuple[str, ...]:
    violations: list[str] = []
    required = (
        "runs-on: ubuntu-24.04",
        '"aiea-sandbox-cert/**"',
        "workflow_dispatch:",
        "permissions:\n  contents: read",
        "docker version",
        "docker pull \"${SANDBOX_IMAGE}\"",
        'python scripts/aiea_research_sandbox_certify.py "${SANDBOX_IMAGE}"',
        "AIEA_RESEARCH_SANDBOX_RUNTIME_CERTIFIED=PASS",
        "actions/upload-artifact@v7.0.1",
        "retention-days: 30",
        "production_deploy_performed\": False",
        "production deployment: NOT PERFORMED",
    )
    for needle in required:
        if needle not in text:
            violations.append(f"missing:{needle}")

    images = _DIGEST_RE.findall(text)
    if len(images) != 1:
        violations.append(f"sandbox-image-digest-count:{len(images)}")

    forbidden = (
        "docker build ",
        "docker push ",
        "docker login ",
        "packages: write",
        "id-token: write",
        "secrets.",
        "/var/run/docker.sock:",
        "runs-on: self-hosted",
        "runs-on: ubuntu-slim",
    )
    lower = text.lower()
    for needle in forbidden:
        if needle.lower() in lower:
            violations.append(f"forbidden:{needle}")

    checkout = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
    if checkout not in text:
        violations.append("checkout-not-sha-pinned")

    return tuple(violations)


def main() -> int:
    text = WORKFLOW.read_text(encoding="utf-8")
    violations = validate_workflow_text(text)
    if violations:
        for item in violations:
            print(f"CI_POLICY_VIOLATION={item}")
        return 1
    print("AIEA_SANDBOX_CI_POLICY=PASS")
    print("CI_RUNTIME_RUNNER=ubuntu-24.04")
    print("CI_PRODUCTION_AUTHORITY=NONE")
    print("CI_IMMUTABLE_IMAGE_DIGEST=PASS")
    print("CI_EVIDENCE_ARTIFACT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
