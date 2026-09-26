"""Phase 14 safe legacy-reference replay foundation tests."""

from __future__ import annotations

import asyncio
import ast
import os
import socket
from datetime import UTC, datetime
from pathlib import Path

import pytest

from apps.core.application.legacy_reference_replay import (
    HistoricalAIState,
    LegacyReferenceReplayHarness,
    ReplayBingXClient,
    ReplaySafetyError,
    ReplayScenario,
    block_outbound_network,
    replay_environment,
)
from apps.core.application.shadow_parity import (
    ShadowEvidenceState,
    ShadowParityDimension,
)

NOW = datetime(2026, 9, 26, 10, 30, tzinfo=UTC)


def make_scenario(*, historical_ai: bool = True) -> ReplayScenario:
    return ReplayScenario(
        as_of=NOW,
        contracts=(
            {
                "symbol": "BTC-USDT",
                "currency": "USDT",
                "status": 1,
                "asset": "BTC",
                "displayName": "BTC/USDT",
                "quantityPrecision": 3,
                "pricePrecision": 1,
            },
            {
                "symbol": "ETH-USDT",
                "currency": "USDT",
                "status": 1,
                "asset": "ETH",
                "displayName": "ETH/USDT",
                "quantityPrecision": 3,
                "pricePrecision": 2,
            },
            {
                "symbol": "NCCOGOLD2USD-USDT",
                "currency": "USDT",
                "status": 1,
                "asset": "NCCOGOLD2USD",
                "displayName": "GOLD",
            },
        ),
        market_tickers_24h=(
            {"symbol": "ETH-USDT", "quoteVolume": "2000"},
            {"symbol": "BTC-USDT", "quoteVolume": "3000"},
            {"symbol": "NCCOGOLD2USD-USDT", "quoteVolume": "999999"},
        ),
        tickers={
            "BTCUSDT": {
                "last_price": 100.0,
                "bid_price": 99.5,
                "ask_price": 100.5,
                "volume_24h": 1000,
            },
            "ETHUSDT": {
                "last_price": 50.0,
                "bid_price": 49.5,
                "ask_price": 50.5,
            },
        },
        klines={
            ("BTCUSDT", "4h"): (
                (1, 95, 101, 94, 100, 1000),
                (2, 100, 102, 99, 101, 1100),
            )
        },
        balance={"USDT": 10000.0, "total_usdt": 10000.0},
        historical_ai_plans=(
            {
                "BTCUSDT": {
                    "approve": True,
                    "position_size": 100.0,
                    "leverage": 3,
                    "stop_loss": 98.0,
                    "take_profit": 104.0,
                    "reasoning": "historical",
                }
            }
            if historical_ai
            else {}
        ),
        commission_rate=0.001,
    )


def test_replay_environment_scrubs_credentials_and_restores_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv("BINGX_API_KEY", "production-key")
    monkeypatch.setenv("BINGX_SECRET_KEY", "production-secret")
    monkeypatch.setenv("GROQ_API_KEY", "production-groq")
    monkeypatch.setenv("DATABASE_URL", "postgresql://production")

    with replay_environment():
        assert "BINGX_API_KEY" not in os.environ
        assert "BINGX_SECRET_KEY" not in os.environ
        assert "GROQ_API_KEY" not in os.environ
        assert os.environ["DATABASE_URL"] == "sqlite+aiosqlite:///:memory:"

    assert os.environ["BINGX_API_KEY"] == "production-key"
    assert os.environ["BINGX_SECRET_KEY"] == "production-secret"
    assert os.environ["GROQ_API_KEY"] == "production-groq"
    assert os.environ["DATABASE_URL"] == "postgresql://production"


def test_replay_environment_rejects_non_ephemeral_database() -> None:
    with pytest.raises(ReplaySafetyError, match="in-memory SQLite"):
        with replay_environment(
            database_url="postgresql://production/nexus_db"
        ):
            pass


def test_network_guard_fails_closed_without_connecting() -> None:
    sock = socket.socket()
    try:
        with block_outbound_network():
            with pytest.raises(ReplaySafetyError, match="outbound network"):
                sock.connect(("127.0.0.1", 9))
    finally:
        sock.close()


def test_dynamic_universe_is_deterministic_crypto_only_and_volume_ranked(
) -> None:
    async def scenario() -> list[str]:
        return await ReplayBingXClient(make_scenario()).get_available_symbols()

    assert asyncio.run(scenario()) == ["BTCUSDT", "ETHUSDT"]
    assert asyncio.run(scenario()) == ["BTCUSDT", "ETHUSDT"]


def test_market_order_fill_position_protection_cancel_and_fee_lifecycle(
) -> None:
    async def scenario():
        client = ReplayBingXClient(make_scenario())
        opened = await client.place_order(
            symbol="BTCUSDT",
            side="BUY",
            size=1.0,
            order_type="MARKET",
            leverage=3,
        )
        protection = await client.set_stop_loss_take_profit(
            symbol="BTCUSDT",
            position_side="LONG",
            size=1.0,
            stop_loss=98.0,
            take_profit=104.0,
        )
        open_orders = await client.get_open_orders("BTCUSDT")
        sl_id = next(
            item["result"]["data"]["orderId"]
            for item in protection
            if item["type"] == "STOP_LOSS"
        )
        cancelled = await client.cancel_order(sl_id, "BTCUSDT")
        after_cancel = await client.get_open_orders("BTCUSDT")
        positions = await client.get_positions()
        commission = await client.get_income(
            symbol="BTCUSDT",
            income_type="COMMISSION",
        )
        return (
            client,
            opened,
            open_orders,
            sl_id,
            cancelled,
            after_cancel,
            positions,
            commission,
        )

    (
        client,
        opened,
        open_orders,
        sl_id,
        cancelled,
        after_cancel,
        positions,
        commission,
    ) = asyncio.run(scenario())

    assert opened["status"] == "FILLED"
    assert opened["order_id"] == "replay-order-000001"
    assert opened["avg_price"] == 100.5
    assert {(item["type"], item["status"]) for item in open_orders} == {
        ("STOP_MARKET", "NEW"),
        ("TAKE_PROFIT_MARKET", "NEW"),
    }
    assert cancelled["code"] == 0
    assert all(item["orderId"] != sl_id for item in after_cancel)
    assert len(positions) == 1
    assert positions[0]["side"] == "LONG"
    assert positions[0]["size"] == 1.0
    assert len(commission) == 1
    assert commission[0]["income"] == pytest.approx(-0.1005)
    assert [event.operation for event in client.write_events] == [
        "place_order",
        "set_protection",
        "set_protection",
        "cancel_order",
    ]


def test_reduce_only_market_close_removes_simulated_hedge_position() -> None:
    async def scenario():
        client = ReplayBingXClient(make_scenario())
        await client.place_order("BTCUSDT", "BUY", 1.0, leverage=2)
        before = await client.get_positions()
        closed = await client.place_order(
            "BTCUSDT",
            "SELL",
            1.0,
            position_side="LONG",
            configure_leverage=False,
            reduce_only=True,
        )
        after = await client.get_positions()
        return before, closed, after

    before, closed, after = asyncio.run(scenario())
    assert len(before) == 1
    assert closed["status"] == "FILLED"
    assert after == []


def test_limit_order_remains_open_until_explicit_deterministic_fill() -> None:
    async def scenario():
        client = ReplayBingXClient(make_scenario())
        placed = await client.place_order(
            "BTCUSDT", "BUY", 0.5, order_type="LIMIT", price=95.0, leverage=2
        )
        before = await client.get_open_orders("BTCUSDT")
        filled = await client.simulate_limit_fill(placed["order_id"])
        after = await client.get_open_orders("BTCUSDT")
        positions = await client.get_positions()
        return placed, before, filled, after, positions

    placed, before, filled, after, positions = asyncio.run(scenario())
    assert placed["status"] == "NEW"
    assert len(before) == 1
    assert filled["status"] == "FILLED"
    assert after == []
    assert positions[0]["entry_price"] == 95.0


def test_historical_ai_gate_never_regenerates_missing_history() -> None:
    verified = LegacyReferenceReplayHarness(
        make_scenario(historical_ai=True)
    ).ai.resolve("BTCUSDT")
    unknown = LegacyReferenceReplayHarness(
        make_scenario(historical_ai=False)
    ).ai.resolve("BTCUSDT")
    assert verified.state is HistoricalAIState.VERIFIED
    assert verified.plan is not None
    assert unknown.state is HistoricalAIState.UNKNOWN
    assert unknown.plan is None
    assert "live regeneration is forbidden" in unknown.reason


def test_reference_evidence_unknown_risk_fails_closed() -> None:
    async def scenario():
        harness = LegacyReferenceReplayHarness(
            make_scenario(historical_ai=False)
        )
        ai = harness.ai.resolve("BTCUSDT")
        await harness.client.place_order("BTCUSDT", "BUY", 1.0, leverage=2)
        return await harness.build_evidence(
            signals_intents={"BTCUSDT": {"signal": "BUY"}},
            risk_decisions=(
                None
                if ai.state is HistoricalAIState.UNKNOWN
                else ai.plan
            ),
            failures_stale_states=[
                {
                    "ai_risk": ai.state.value,
                    "reason": ai.reason,
                }
            ],
        )

    evidence = asyncio.run(scenario())
    assert evidence.state is ShadowEvidenceState.CURRENT
    assert len(evidence.dimensions) == 8
    assert evidence.dimensions[ShadowParityDimension.RISK_DECISIONS] is None
    failures = evidence.dimensions[ShadowParityDimension.FAILURES_STALE_STATES]
    assert failures == [
        {
            "ai_risk": "UNKNOWN",
            "reason": (
                "historical Groq output is unavailable; "
                "live regeneration is forbidden"
            ),
        }
    ]


def test_repeat_run_is_deterministic() -> None:
    async def run_once():
        harness = LegacyReferenceReplayHarness(make_scenario())
        await harness.client.place_order("BTCUSDT", "BUY", 1.0, leverage=3)
        await harness.client.set_stop_loss_take_profit(
            "BTCUSDT", "LONG", 1.0, stop_loss=98.0, take_profit=104.0
        )
        return await harness.build_evidence(
            signals_intents={
                "BTCUSDT": {
                    "signal": "BUY",
                    "strategy": "breakout",
                }
            },
            risk_decisions={"BTCUSDT": harness.ai.resolve("BTCUSDT").plan},
        )

    first = asyncio.run(run_once())
    second = asyncio.run(run_once())
    assert first == second


def test_known_legacy_grid_cancel_argument_reversal_is_not_silently_accepted(
) -> None:
    async def scenario():
        client = ReplayBingXClient(make_scenario())
        placed = await client.place_order(
            "BTCUSDT", "BUY", 0.5, order_type="LIMIT", price=95.0
        )
        # Frozen GridAgent.remove_grid calls cancel_order(symbol, order_id),
        # while the BingX client contract is cancel_order(order_id, symbol).
        # Replay preserves that contract, so the defect remains observable.
        result = await client.cancel_order("BTCUSDT", placed["order_id"])
        open_orders = await client.get_open_orders("BTCUSDT")
        return result, open_orders

    result, open_orders = asyncio.run(scenario())
    assert result["error"] == "order not found"
    assert len(open_orders) == 1


def test_replay_module_contains_no_http_or_exchange_sdk_imports() -> None:
    module_path = Path("apps/core/application/legacy_reference_replay.py")
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    assert roots.isdisjoint({"requests", "httpx", "aiohttp", "groq", "ccxt"})
