from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from infra.persistence.repositories.control_plane_read import ControlPlaneReadRepository

NOW = datetime(2026, 9, 27, 18, 0, tzinfo=UTC)


class _ScalarRows:
    def __init__(self, rows: list[object]) -> None:
        self._rows = rows

    def all(self) -> list[object]:
        return self._rows


class _Rows:
    def __init__(self, rows: list[object]) -> None:
        self._rows = rows

    def scalars(self) -> _ScalarRows:
        return _ScalarRows(self._rows)


class _Pairs:
    def __init__(self, rows: list[tuple[object, object]]) -> None:
        self._rows = rows

    def all(self) -> list[tuple[object, object]]:
        return self._rows


def _position() -> SimpleNamespace:
    return SimpleNamespace(
        native_symbol="BTC-USDT",
        side="LONG",
        current_quantity=Decimal("0.5"),
        average_entry_price=Decimal("60000"),
        status="OPEN",
        venue_id="BINGX",
        account_value=7,
    )


def _order() -> SimpleNamespace:
    return SimpleNamespace(
        order_id="order-1",
        native_symbol="BTC-USDT",
        side="BUY",
        order_type="LIMIT",
        requested_quantity=Decimal("0.5"),
        filled_quantity=Decimal("0.2"),
        average_fill_price=Decimal("60100"),
        limit_price=Decimal("60050"),
        local_status="PARTIALLY_FILLED",
        venue_id="BINGX",
        account_value=7,
        updated_at=NOW,
    )


def _fill() -> SimpleNamespace:
    return SimpleNamespace(
        fill_id="fill-1",
        order_id="order-1",
        quantity=Decimal("0.2"),
        price=Decimal("60100"),
        fee=Decimal("0.01"),
        fee_currency="USDT",
        venue_id="BINGX",
        account_value=7,
        executed_at=NOW,
    )


def _recon_event(event_type: str, payload: dict[str, object]) -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        event_type=event_type,
        payload=payload,
        native_symbol="BTC-USDT",
        venue_id="BINGX",
        occurred_at=NOW,
    )


def test_overview_requires_active_workspace_membership() -> None:
    async def scenario() -> None:
        session = AsyncSession()
        session.get = AsyncMock(return_value=None)  # type: ignore[method-assign]
        with pytest.raises(PermissionError, match="active workspace"):
            await ControlPlaneReadRepository(session).overview(
                workspace_id="ws-a", user_id=7
            )
        await session.close()

    asyncio.run(scenario())


def test_overview_projects_real_canonical_rows_without_invented_risk() -> None:
    async def scenario():
        session = AsyncSession()
        session.get = AsyncMock(  # type: ignore[method-assign]
            return_value=SimpleNamespace(active=True)
        )
        order = _order()
        discrepancy = _recon_event(
            "RECONCILIATION_DISCREPANCY",
            {
                "discrepancy_id": "disc-1",
                "kind": "POSITION_QUANTITY_DRIFT",
                "subject": "POSITION",
                "local_value": "0.5",
                "venue_value": "0.4",
            },
        )
        terminal = _recon_event(
            "RECONCILIATION_COMPLETED",
            {"result_state": "DISCREPANCY"},
        )
        terminal.id = 2
        session.execute = AsyncMock(  # type: ignore[method-assign]
            side_effect=[
                _Rows([_position()]),
                _Rows([order]),
                _Pairs([(_fill(), order)]),
                _Rows([discrepancy, terminal]),
                _Rows([]),
            ]
        )
        value = await ControlPlaneReadRepository(session).overview(
            workspace_id="ws-a", user_id=7
        )
        await session.close()
        return value

    value = asyncio.run(scenario())
    assert value.open_position_count == 1
    assert value.open_order_count == 1
    assert value.positions[0].symbol == "BTC-USDT"
    assert value.orders[0].filled_quantity == Decimal("0.2")
    assert value.fills[0].fill_id == "fill-1"
    assert value.reconciliation_state == "DISCREPANCY"
    assert value.reconciliation_discrepancy_count == 1
    assert value.reconciliation_discrepancies[0].kind == "POSITION_QUANTITY_DRIFT"
    assert value.portfolio_state == "UNAVAILABLE"
    assert value.risk_state == "UNAVAILABLE"


def test_resolved_discrepancy_is_not_reported_as_active() -> None:
    async def scenario():
        session = AsyncSession()
        session.get = AsyncMock(  # type: ignore[method-assign]
            return_value=SimpleNamespace(active=True)
        )
        discrepancy = _recon_event(
            "RECONCILIATION_DISCREPANCY",
            {"discrepancy_id": "disc-1", "kind": "ORDER_STATE_DRIFT", "subject": "ORDER"},
        )
        resolved = _recon_event(
            "RECONCILIATION_RESOLVED",
            {"discrepancy_id": "disc-1"},
        )
        resolved.id = 2
        terminal = _recon_event(
            "RECONCILIATION_COMPLETED",
            {"result_state": "MATCHED"},
        )
        terminal.id = 3
        session.execute = AsyncMock(  # type: ignore[method-assign]
            side_effect=[
                _Rows([]),
                _Rows([]),
                _Pairs([]),
                _Rows([discrepancy, resolved, terminal]),
                _Rows([]),
            ]
        )
        value = await ControlPlaneReadRepository(session).overview(
            workspace_id="ws-a", user_id=7
        )
        await session.close()
        return value

    value = asyncio.run(scenario())
    assert value.reconciliation_state == "MATCHED"
    assert value.reconciliation_discrepancy_count == 0
    assert value.reconciliation_discrepancies == ()


def _risk_snapshot_model(*, observed_at: datetime = NOW, equity: str = "9000") -> SimpleNamespace:
    return SimpleNamespace(
        snapshot_id=f"risk-{observed_at.isoformat()}",
        user_id=7,
        observation_state="CURRENT",
        trading_state="ACTIVE",
        equity=Decimal(equity),
        daily_start_equity=Decimal("10000"),
        rolling_peak_equity=Decimal("12000"),
        exposures_json='[{"account_value":7,"account_venue_id":"BINGX","asset_class":"CRYPTO","correlation_cluster":"CRYPTO-MAJOR","instrument_type":"PERPETUAL","instrument_venue_id":"BINGX","margin_used":"500","native_symbol":"BTC-USDT","position_group_id":"g-1","settlement_currency":"USDT","signed_notional":"2500","strategy":"trend"}]',
        limits_json='{"hedge_tolerance":"0.05","max_account_exposure":"10000","max_correlation_cluster_exposure":"12000","max_currency_concentration":"1","max_daily_drawdown":"0.10","max_expected_slippage_bps":"25","max_gross_exposure":"20000","max_instrument_exposure":"6000","max_leverage":"5","max_margin_utilization":"0.8","max_net_exposure":"15000","max_open_position_groups":10,"max_order_liquidity_ratio":"0.10","max_rolling_drawdown":"0.20","max_strategy_exposure":"10000","max_venue_exposure":"15000"}',
        source="risk-runtime",
        observed_at=observed_at,
        recorded_at=observed_at,
    )


def test_overview_projects_persisted_portfolio_and_risk_snapshot() -> None:
    async def scenario():
        session = AsyncSession()
        session.get = AsyncMock(return_value=SimpleNamespace(active=True))  # type: ignore[method-assign]
        older = _risk_snapshot_model(observed_at=NOW, equity="9000")
        newer_time = datetime(2026, 9, 27, 18, 5, tzinfo=UTC)
        newer = _risk_snapshot_model(observed_at=newer_time, equity="9500")
        session.execute = AsyncMock(  # type: ignore[method-assign]
            side_effect=[_Rows([]), _Rows([]), _Pairs([]), _Rows([]), _Rows([newer, older])]
        )
        value = await ControlPlaneReadRepository(session).overview(workspace_id="ws-a", user_id=7)
        await session.close()
        return value

    value = asyncio.run(scenario())
    assert value.portfolio_state == "CURRENT"
    assert value.risk_state == "ACTIVE"
    assert value.portfolio is not None
    assert value.portfolio.equity == Decimal("9500")
    assert value.portfolio.daily_pnl == Decimal("-500")
    assert value.portfolio.gross_exposure == Decimal("2500")
    assert value.risk is not None
    assert value.risk.trading_state == "ACTIVE"
    assert value.risk.headline_utilization > Decimal("0")
    assert [point.equity for point in value.portfolio_history] == [Decimal("9000"), Decimal("9500")]
