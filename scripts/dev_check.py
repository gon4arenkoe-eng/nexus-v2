from __future__ import annotations

from pathlib import Path
import json
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "pyproject.toml",
    ".python-version",
    ".devcontainer/devcontainer.json",
    "scripts/dev_check.py",
    "docs/runbooks/LOCAL_DEVELOPMENT.md",
    "packages/contracts/product_access.py",
    "packages/contracts/workspace.py",
    "tests/test_shared_contract_compatibility.py",
    "tests/test_contract_product_access.py",
    "tests/test_contract_workspace.py",
)

FORBIDDEN_DEVCONTAINER_MARKERS = (
    "docker.sock",
    "/var/run/docker.sock",
    "kubectl",
    "docker push",
    "ghcr.io/",
    "ssh ",
    "production credential",
    "exchange api key",
)

def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)

if sys.version_info[:2] != (3, 13):
    fail(f"Python 3.13 required, running {sys.version.split()[0]}")

for rel in REQUIRED_FILES:
    if not (ROOT / rel).is_file():
        fail(f"missing local development baseline file: {rel}")

python_version = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
if python_version != "3.13":
    fail(f".python-version must be 3.13, got {python_version!r}")

with (ROOT / "pyproject.toml").open("rb") as fh:
    pyproject = tomllib.load(fh)

requires_python = pyproject.get("project", {}).get("requires-python")
if requires_python != ">=3.13,<3.14":
    fail(f"unexpected requires-python: {requires_python!r}")

nexus_cfg = pyproject.get("tool", {}).get("nexus", {})
if nexus_cfg.get("phase") != 1:
    fail("tool.nexus.phase must be 1")
if nexus_cfg.get("production_build_allowed") is not False:
    fail("production_build_allowed must be false")
if nexus_cfg.get("production_deploy_allowed") is not False:
    fail("production_deploy_allowed must be false")

dev_path = ROOT / ".devcontainer/devcontainer.json"
dev = json.loads(dev_path.read_text(encoding="utf-8"))
if dev.get("containerEnv", {}).get("NEXUS_ENV") != "development":
    fail("devcontainer must set NEXUS_ENV=development")
if dev.get("containerEnv", {}).get("NEXUS_LIVE_AUTHORITY") != "disabled":
    fail("devcontainer must keep NEXUS_LIVE_AUTHORITY=disabled")

dev_text = dev_path.read_text(encoding="utf-8").lower()
for marker in FORBIDDEN_DEVCONTAINER_MARKERS:
    if marker in dev_text:
        fail(f"forbidden devcontainer authority marker present: {marker}")

ci_text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
if "python scripts/dev_check.py" not in ci_text:
    fail("CI must execute scripts/dev_check.py")

print("[OK] NEXUS_V2_PHASE1_LOCAL_DEV_BASELINE_OK")
print(f"[OK] python={sys.version.split()[0]}")
print("[OK] Python contract=3.13")
print("[OK] devcontainer environment=development")
print("[OK] live authority=disabled")
print("[OK] production build/deploy authority=false")
