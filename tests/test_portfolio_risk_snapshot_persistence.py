from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

pytest.importorskip("aiosqlite")

from apps.core.domain.portfolio_risk import (  # noqa: E402
    PortfolioExposure,
    PortfolioRiskLimits,
    PortfolioRiskSnapshot,
    PortfolioRiskState,
    RiskObservationState,
)
from infra.persistence.base import PersistenceBase  # noqa: E402
from infra.persistence.models import PortfolioRiskSnapshotModel  # noqa: E402
from infra.persistence.repositories.portfolio_risk_snapshot import (  # noqa: E402
    PortfolioRiskSnapshotRepository,
)
from packages.contracts.identities import (  # noqa: E402
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)

NOW = datetime(2026, 9, 27, 19, 0, tzinfo=UTC)


def _limits() -> PortfolioRiskLimits:
    return PortfolioRiskLimits(
        max_open_position_groups=10,
        max_gross_exposure=Decimal("20000"),
        max_net_exposure=Decimal("15000"),
        max_account_exposure=Decimal("10000"),
        max_venue_exposure=Decimal("15000"),
        max_strategy_exposure=Decimal("10000"),
        max_instrument_exposure=Decimal("6000"),
        max_currency_concentration=Decimal("1"),
        max_correlation_cluster_exposure=Decimal("12000"),
        max_leverage=Decimal("5"),
        max_margin_utilization=Decimal("0.8"),
        max_daily_drawdown=Decimal("0.05"),
        max_rolling_drawdown=Decimal("0.10"),
        max_order_liquidity_ratio=Decimal("0.10"),
        max_expected_slippage_bps=Decimal("25"),
    )


def _snapshot(*, user_id: int, observed_at: datetime, equity: str) -> PortfolioRiskSnapshot:
    venue = VenueId("BINGX")
    exposure = PortfolioExposure(
        position_group_id=f"g-{user_id}",
        account_id=AccountId(venue_id=venue, value=user_id),
        instrument_id=InstrumentId(
            venue_id=venue,
            native_symbol="BTC-USDT",
            instrument_type=InstrumentType.PERPETUAL,
            asset_class=AssetClass.CRYPTO,
        ),
        strategy="trend",
        settlement_currency="USDT",
        correlation_cluster="CRYPTO-MAJOR",
        signed_notional=Decimal("2500"),
        margin_used=Decimal("500"),
    )
    return PortfolioRiskSnapshot(
        user_id=user_id,
        observation_state=RiskObservationState.CURRENT,
        trading_state=PortfolioRiskState.ACTIVE,
        equity=Decimal(equity),
        daily_start_equity=Decimal("10000"),
        rolling_peak_equity=Decimal("12000"),
        exposures=(exposure,),
        observed_at=observed_at,
    )


def test_snapshot_history_survives_fresh_session_and_is_user_isolated() -> None:
    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(PersistenceBase.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        limits = _limits()
        first = _snapshot(user_id=7, observed_at=NOW, equity="10000")
        second = _snapshot(user_id=7, observed_at=NOW + timedelta(minutes=5), equity="10100")
        other = _snapshot(user_id=8, observed_at=NOW + timedelta(minutes=10), equity="9999")
        async with factory() as session:
            repo = PortfolioRiskSnapshotRepository(session)
            first_id = await repo.append(snapshot=first, limits=limits, source="risk-runtime", recorded_at=NOW)
            duplicate_id = await repo.append(snapshot=first, limits=limits, source="risk-runtime", recorded_at=NOW + timedelta(seconds=1))
            await repo.append(snapshot=second, limits=limits, source="risk-runtime", recorded_at=NOW + timedelta(minutes=5))
            await repo.append(snapshot=other, limits=limits, source="risk-runtime", recorded_at=NOW + timedelta(minutes=10))
            await session.commit()
        async with factory() as session:
            repo = PortfolioRiskSnapshotRepository(session)
            own = await repo.list_recent_for_user(user_id=7)
            foreign = await repo.list_recent_for_user(user_id=8)
            latest = await repo.latest_for_user(user_id=7)
        await engine.dispose()
        return first_id, duplicate_id, own, foreign, latest

    first_id, duplicate_id, own, foreign, latest = asyncio.run(scenario())
    assert first_id == duplicate_id
    assert [item.snapshot.equity for item in own] == [Decimal("10100"), Decimal("10000")]
    assert [item.snapshot.user_id for item in own] == [7, 7]
    assert [item.snapshot.user_id for item in foreign] == [8]
    assert latest is not None
    assert latest.snapshot.equity == Decimal("10100")
    assert latest.snapshot.exposures[0].instrument_id.native_symbol == "BTC-USDT"
    assert latest.limits.max_leverage == Decimal("5")


def test_snapshot_model_is_registered_on_canonical_metadata() -> None:
    assert PortfolioRiskSnapshotModel.__tablename__ == "portfolio_risk_snapshots"
    assert "portfolio_risk_snapshots" in PersistenceBase.metadata.tables


def test_portfolio_risk_migration_is_current_linear_head() -> None:
    from infra.persistence.migrations.versions import f2c4e6a8b013_add_portfolio_risk_snapshots as migration

    assert migration.revision == "f2c4e6a8b013"
    assert migration.down_revision == "e9b1c7d3a246"
