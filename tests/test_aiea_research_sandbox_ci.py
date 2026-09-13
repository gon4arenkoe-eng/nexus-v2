from pathlib import Path

from infra.github.aiea_research_sandbox_ci_check import validate_workflow_text


WORKFLOW = Path(".github/workflows/aiea-research-sandbox-certification.yml")


def test_runtime_certification_workflow_is_policy_compliant() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert validate_workflow_text(text) == ()


def test_runtime_certification_workflow_has_no_production_write_authority() -> None:
    text = WORKFLOW.read_text(encoding="utf-8").lower()
    assert "packages: write" not in text
    assert "id-token: write" not in text
    assert "secrets." not in text
    assert "docker push " not in text
    assert "docker build " not in text
    assert "docker login " not in text


def test_runtime_certification_is_digest_pinned_and_branch_scoped() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "python@sha256:" in text
    assert '"aiea-sandbox-cert/**"' in text
    assert "AIEA_RESEARCH_SANDBOX_RUNTIME_CERTIFIED=PASS" in text
    assert "retention-days: 30" in text
