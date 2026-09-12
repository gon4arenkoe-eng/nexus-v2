from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "release-image.yml"


def _workflow_text() -> str:
    if not WORKFLOW.exists():
        raise SystemExit("release-image.yml missing")
    return WORKFLOW.read_text(encoding="utf-8")


def main() -> int:
    text = _workflow_text()
    required = (
        "docker/build-push-action@",
        "push: true",
        "sbom: true",
        "provenance: mode=max",
    )
    missing = [token for token in required if token not in text]
    if missing:
        raise SystemExit(
            "SUPPLY_CHAIN_EVIDENCE_POLICY=FAIL missing=" + ",".join(missing)
        )

    forbidden = (
        "appleboy/ssh-action",
        "scp-action",
        "ssh-action",
        "docker build ",
        "docker compose build",
    )
    found = [token for token in forbidden if token.lower() in text.lower()]
    if found:
        raise SystemExit(
            "SUPPLY_CHAIN_EVIDENCE_POLICY=FAIL forbidden=" + ",".join(found)
        )

    print("SUPPLY_CHAIN_EVIDENCE_POLICY=PASS")
    print("SBOM_ATTESTATION=DEFINED")
    print("PROVENANCE_ATTESTATION=MODE_MAX")
    print("ATTESTATION_SUBJECT=RELEASE_IMAGE")
    print("PRODUCTION_DEPLOY_AUTHORITY=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
