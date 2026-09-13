"""Static safety tests for the VST read-only certification runner."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "certify_bingx_vst_readonly.py"


def test_certification_script_is_read_only() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    forbidden = (
        "submit_order(",
        "cancel_order(",
        "close_position",
        "allow_demo_writes=True",
        "open-api.bingx.com",
        "open-api.bingx.pro",
    )
    for marker in forbidden:
        assert marker not in text


def test_certification_script_requires_env_secrets_not_cli_values() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'BINGX_VST_API_KEY' in text
    assert 'BINGX_VST_SECRET_KEY' in text
    assert "argparse" not in text
    assert "api_key=" in text
    assert "secret_key=" in text


def test_evidence_does_not_include_secret_fields() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    evidence_block = text.split(
        "class BingXVstReadOnlyEvidence:",
        maxsplit=1,
    )[1].split("async def _run", maxsplit=1)[0]
    assert "api_key" not in evidence_block
    assert "secret" not in evidence_block
    assert "signature" not in evidence_block
    assert "raw" not in evidence_block
