from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    "NEXUS_V2_MASTER_PLAN.md",
    "NEXUS_V2_FUNCTIONAL_INVENTORY.md",
    "NEXUS_PROJECT_AUDIT.md",
    "docs/architecture/DEPENDENCY_BOUNDARIES.md",
    ".gitattributes",
    ".editorconfig",
    ".gitignore",
    ".github/workflows/ci.yml",
]

REQUIRED_DIRS = [
    "apps/core",
    "apps/intelligence",
    "apps/aiea",
    "apps/web",
    "workers/aiea_research",
    "packages/contracts",
    "packages/testkit",
    "packages/observability",
    "adapters/bingx",
    "adapters/binance",
    "adapters/bybit",
    "adapters/okx",
    "infra/compose",
    "infra/migrations",
    "infra/github",
    "infra/deploy",
    "docs/architecture",
    "docs/runbooks",
    "docs/adr",
]

FORBIDDEN_EXACT_NAMES = {
    ".env",
    "id_rsa",
    "id_ed25519",
}

FORBIDDEN_NAME_FRAGMENTS = (
    "before_secret_redaction",
    "private_key",
    "credentials_backup",
)

def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)

for rel in REQUIRED_FILES:
    if not (ROOT / rel).is_file():
        fail(f"missing required file: {rel}")

for rel in REQUIRED_DIRS:
    if not (ROOT / rel).is_dir():
        fail(f"missing required directory: {rel}")

violations: list[str] = []
for path in ROOT.rglob("*"):
    if ".git" in path.parts:
        continue
    name = path.name.lower()
    if name in FORBIDDEN_EXACT_NAMES:
        violations.append(str(path.relative_to(ROOT)))
        continue
    if any(fragment in name for fragment in FORBIDDEN_NAME_FRAGMENTS):
        violations.append(str(path.relative_to(ROOT)))

if violations:
    fail("forbidden secret-sensitive paths present: " + ", ".join(sorted(violations)))

workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
for forbidden in ("deploy", "ghcr.io", "docker push", "kubectl", "ssh "):
    if forbidden in workflow.lower():
        fail(f"Phase 0 CI contains forbidden deployment authority marker: {forbidden}")

policy = (ROOT / "docs/architecture/DEPENDENCY_BOUNDARIES.md").read_text(encoding="utf-8")
required_policy_markers = (
    "Core domain → exchange SDK/client.",
    "AIEA → exchange credentials.",
    "UI → direct database access.",
    "Raw venue fields → canonical Core domain.",
)
for marker in required_policy_markers:
    if marker not in policy:
        fail(f"dependency policy marker missing: {marker}")

print("[OK] NEXUS_V2_PHASE0_REPO_BASELINE_CHECK_OK")
print(f"[OK] required_files={len(REQUIRED_FILES)} required_dirs={len(REQUIRED_DIRS)}")
print("[OK] no deployment authority in Phase 0 CI")
print("[OK] no forbidden secret-sensitive paths detected")
