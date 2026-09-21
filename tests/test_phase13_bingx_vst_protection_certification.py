from __future__ import annotations

from decimal import Decimal

import pytest

from scripts.certify_bingx_vst_controlled_execution import (
    _certification_mode,
)


def test_certification_mode_defaults_to_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "NEXUS_BINGX_VST_CERT_MODE",
        raising=False,
    )

    assert _certification_mode() == "LIMIT"


def test_certification_mode_accepts_protection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "NEXUS_BINGX_VST_CERT_MODE",
        "PROTECTION",
    )

    assert _certification_mode() == "PROTECTION"


def test_certification_mode_rejects_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "NEXUS_BINGX_VST_CERT_MODE",
        "LIVE",
    )

    with pytest.raises(
        RuntimeError,
        match="LIMIT or PROTECTION",
    ):
        _certification_mode()


def test_protection_price_invariant() -> None:
    stop = Decimal("50000")
    entry = Decimal("60000")
    take_profit = Decimal("70000")

    assert stop < entry < take_profit
