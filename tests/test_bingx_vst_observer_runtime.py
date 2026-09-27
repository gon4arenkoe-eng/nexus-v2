from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from scripts import bingx_vst_observer_runtime as runtime


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "bingx_vst_observer_runtime.py"


def test_runtime_source_has_no_write_path() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    for marker in ("submit_order(", "cancel_order(", "allow_demo_writes=True", "ExecutionCoordinator"):
        assert marker not in text
    assert "BingXVstReadOnlyHttpTransport" in text


def test_runtime_authority_is_fail_closed() -> None:
    payload = runtime._payload(None)
    assert payload["ready"] is False
    assert payload["production_authority"] is False
    assert payload["strategy_execution_allowed"] is False


def test_current_snapshot_is_ready_but_not_execution_authorized() -> None:
    snapshot = runtime.ObserverSnapshot(
        environment="BINGX_VST",
        symbol="BTCUSDT",
        observed_at="2026-09-20T00:00:00+00:00",
        source_state="CURRENT",
        account_query="PASS",
        open_orders_query="PASS",
        positions_query="PASS",
        fills_query="PASS",
        balance_assets=("VST",),
        open_order_count=2,
        position_count=15,
        fill_count=0,
        writes_attempted=False,
        production_authority=False,
        strategy_execution_allowed=False,
    )
    payload = runtime._payload(snapshot)
    assert payload["ready"] is True
    assert payload["status"] == "RUNNING"
    assert payload["strategy_execution_allowed"] is False


def test_failure_is_explicit_and_not_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BINGX_VST_SYMBOL", "BTCUSDT")
    snapshot = runtime._failed_snapshot(RuntimeError("venue unavailable"))
    payload = runtime._payload(snapshot)
    assert snapshot.source_state == "UNAVAILABLE"
    assert payload["status"] == "DEGRADED"
    assert payload["ready"] is False
    assert "venue unavailable" in str(payload["error"])


def test_interval_rejects_subsecond_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NEXUS_OBSERVER_INTERVAL_SECONDS", "0.5")
    with pytest.raises(RuntimeError, match=">= 1"):
        runtime._interval_seconds()


def test_secret_values_are_not_part_of_snapshot_contract() -> None:
    fields = runtime.ObserverSnapshot.__dataclass_fields__
    assert "api_key" not in fields
    assert "secret_key" not in fields
    assert "signature" not in fields


def test_observer_is_long_running_not_one_shot() -> None:
    source = inspect.getsource(runtime.observer_loop)
    assert "while not stop.is_set()" in source
    assert "stop.wait(interval)" in source


def test_portfolio_risk_recording_is_opt_in_and_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NEXUS_VST_PORTFOLIO_RISK_RECORDING", raising=False)
    assert runtime._risk_recording_enabled() is False

    monkeypatch.setenv("NEXUS_VST_PORTFOLIO_RISK_RECORDING", "ENABLED")
    assert runtime._risk_recording_enabled() is True

    snapshot = runtime.ObserverSnapshot(
        environment="BINGX_VST",
        symbol="BTCUSDT",
        observed_at="2026-09-20T00:00:00+00:00",
        source_state="CURRENT",
        account_query="PASS",
        open_orders_query="PASS",
        positions_query="PASS",
        fills_query="PASS",
        balance_assets=("VST",),
        open_order_count=0,
        position_count=1,
        fill_count=0,
        writes_attempted=False,
        production_authority=False,
        strategy_execution_allowed=False,
        portfolio_risk_recording="FAIL",
        portfolio_risk_recording_error="RuntimeError: database unavailable",
    )
    payload = runtime._payload(snapshot)
    assert payload["ready"] is False
    assert payload["status"] == "DEGRADED"
    assert payload["production_authority"] is False


def test_portfolio_risk_limits_require_explicit_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NEXUS_PORTFOLIO_RISK_LIMITS_JSON", raising=False)
    with pytest.raises(RuntimeError, match="required environment variable"):
        runtime._portfolio_risk_limits()


def test_real_snapshot_recorder_persists_canonical_venue_values(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import asyncio
    from datetime import UTC, datetime
    from decimal import Decimal

    from apps.core.ports.venue import VenuePosition, VenuePositionSide
    from apps.core.ports.venue_account import (
        VenueAccountObservationState,
        VenueAccountState,
        VenueBalance,
    )
    from infra.persistence.models.portfolio_risk import PortfolioRiskSnapshotModel
    from infra.persistence.repositories.portfolio_risk_snapshot import (
        PortfolioRiskSnapshotRepository,
    )
    from infra.persistence.session import (
        create_persistence_engine,
        create_session_factory,
    )
    from packages.contracts.identities import (
        AccountId,
        AssetClass,
        InstrumentId,
        InstrumentType,
    )
    from adapters.bingx.venue import BINGX_VENUE_ID

    async def scenario() -> None:
        db = tmp_path / "risk.sqlite"
        url = f"sqlite+aiosqlite:///{db}"
        engine = create_persistence_engine(url)
        async with engine.begin() as connection:
            await connection.run_sync(
                PortfolioRiskSnapshotModel.__table__.create
            )
        await engine.dispose()

        limits = {
            "max_open_position_groups": 10,
            "max_gross_exposure": "200000",
            "max_net_exposure": "150000",
            "max_account_exposure": "200000",
            "max_venue_exposure": "200000",
            "max_strategy_exposure": "200000",
            "max_instrument_exposure": "150000",
            "max_currency_concentration": "1",
            "max_correlation_cluster_exposure": "200000",
            "max_leverage": "20",
            "max_margin_utilization": "0.9",
            "max_daily_drawdown": "0.1",
            "max_rolling_drawdown": "0.2",
            "max_order_liquidity_ratio": "0.1",
            "max_expected_slippage_bps": "25",
        }
        monkeypatch.setenv("NEXUS_V2_DATABASE_URL", url)
        monkeypatch.setenv("NEXUS_CONTROL_PLANE_USER_ID", "7")
        monkeypatch.setenv(
            "NEXUS_PORTFOLIO_RISK_LIMITS_JSON",
            __import__("json").dumps(limits),
        )
        monkeypatch.setenv("NEXUS_VST_EQUITY_ASSET", "VST")

        observed_at = datetime.now(UTC)
        account_id = AccountId(venue_id=BINGX_VENUE_ID, value=1)
        instrument = InstrumentId(
            venue_id=BINGX_VENUE_ID,
            native_symbol="BTCUSDT",
            instrument_type=InstrumentType.PERPETUAL,
            asset_class=AssetClass.CRYPTO,
        )
        account = VenueAccountState(
            account_id=account_id,
            state=VenueAccountObservationState.CURRENT,
            observed_at=observed_at,
            balances=(
                VenueBalance(
                    asset="VST",
                    total=Decimal("100000"),
                    available=Decimal("90000"),
                ),
            ),
        )
        positions = (
            VenuePosition(
                account_id=account_id,
                instrument_id=instrument,
                side=VenuePositionSide.LONG,
                quantity=Decimal("0.5"),
                entry_price=Decimal("60000"),
                mark_price=Decimal("62000"),
                leverage=Decimal("10"),
                observed_at=observed_at,
            ),
        )

        snapshot_id = await runtime._record_portfolio_risk_snapshot(
            account=account,
            positions=positions,
        )
        assert len(snapshot_id) == 64

        check_engine = create_persistence_engine(url)
        factory = create_session_factory(check_engine)
        async with factory() as session:
            stored = await PortfolioRiskSnapshotRepository(
                session
            ).latest_for_user(user_id=7)
            assert stored is not None
            assert stored.source == "BINGX_VST_OBSERVER_REAL"
            assert stored.snapshot.equity == Decimal("100000")
            assert stored.snapshot.trading_state.value == "HALTED"
            assert stored.snapshot.exposures[0].signed_notional == Decimal(
                "31000"
            )
            assert stored.snapshot.exposures[0].margin_used == Decimal(
                "3100"
            )
        await check_engine.dispose()

    asyncio.run(scenario())
