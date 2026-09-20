"""Safety tests for BingX VST controlled execution certification."""

from __future__ import annotations

import asyncio
from decimal import Decimal

import pytest

import scripts.certify_bingx_vst_controlled_execution as cert
from apps.core.ports.venue import VenueOrderState
from packages.contracts.identities import VenueOrderId


def test_requires_explicit_controlled_write_enablement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "NEXUS_BINGX_VST_CONTROLLED_WRITE",
        raising=False,
    )

    with pytest.raises(
        RuntimeError,
        match="explicit certification enablement",
    ):
        cert._require_certification_enablement()


def test_enablement_requires_exact_vst_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "NEXUS_BINGX_VST_CONTROLLED_WRITE",
        "YES",
    )

    with pytest.raises(
        RuntimeError,
        match="explicit certification enablement",
    ):
        cert._require_certification_enablement()


def test_client_order_id_is_certification_scoped() -> None:
    first = cert._client_order_id()
    second = cert._client_order_id()

    assert first.value.startswith("nexus-cert-")
    assert second.value.startswith("nexus-cert-")
    assert first != second


def test_source_has_no_real_bingx_hosts_or_database_access() -> None:
    source = open(cert.__file__, encoding="utf-8").read()

    assert "https://open-api.bingx.com" not in source
    assert "https://open-api.bingx.pro" not in source
    assert "sqlalchemy" not in source.lower()
    assert "postgres" not in source.lower()
    assert "ExecutionCoordinator" not in source


def test_runner_uses_canonical_adapter_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "NEXUS_BINGX_VST_CONTROLLED_WRITE",
        "I_UNDERSTAND_VST_ONLY",
    )
    monkeypatch.setenv("BINGX_VST_API_KEY", "test-key")
    monkeypatch.setenv("BINGX_VST_SECRET_KEY", "test-secret")
    monkeypatch.setenv("BINGX_VST_SYMBOL", "BTCUSDT")
    monkeypatch.setenv("BINGX_VST_CERT_QUANTITY", "0.0001")
    monkeypatch.setenv("BINGX_VST_CERT_LIMIT_PRICE", "1")

    calls: list[str] = []

    class FakeAdapter:
        def __init__(self, **kwargs: object) -> None:
            pass

        async def submit_order(self, request):
            calls.append("submit")
            assert request.client_order_id.value.startswith(
                "nexus-cert-"
            )
            assert request.quantity == Decimal("0.0001")
            assert request.limit_price == Decimal("1")
            assert request.reduce_only is False

            return type(
                "Result",
                (),
                {
                    "state": VenueOrderState.ACCEPTED,
                    "venue_order_id": VenueOrderId("cert-venue-1"),
                },
            )()

        async def get_order(self, **kwargs):
            calls.append("observe")
            return type(
                "Result",
                (),
                {
                    "state": VenueOrderState.ACCEPTED,
                },
            )()

        async def cancel_order(self, **kwargs):
            calls.append("cancel")
            return type(
                "Result",
                (),
                {
                    "state": VenueOrderState.CANCELLED,
                },
            )()

    monkeypatch.setattr(cert, "BingXVenueAdapter", FakeAdapter)

    evidence = asyncio.run(cert._run())

    assert calls == ["submit", "observe", "cancel"]
    assert evidence.environment == "BINGX_VST"
    assert evidence.production_environment_used is False
    assert evidence.writes_attempted is True
    assert evidence.cancelled_state == "CANCELLED"


def test_invalid_quantity_fails_before_adapter_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "NEXUS_BINGX_VST_CONTROLLED_WRITE",
        "I_UNDERSTAND_VST_ONLY",
    )
    monkeypatch.setenv("BINGX_VST_API_KEY", "test-key")
    monkeypatch.setenv("BINGX_VST_SECRET_KEY", "test-secret")
    monkeypatch.setenv("BINGX_VST_CERT_LIMIT_PRICE", "1")
    monkeypatch.setenv("BINGX_VST_CERT_QUANTITY", "0")

    with pytest.raises(
        RuntimeError,
        match="quantity must be positive",
    ):
        asyncio.run(cert._run())
