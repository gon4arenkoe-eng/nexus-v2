"""Persistence boundary for immutable canonical Portfolio Risk snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.domain.portfolio_risk import (
    PortfolioExposure,
    PortfolioRiskLimits,
    PortfolioRiskSnapshot,
    PortfolioRiskState,
    RiskObservationState,
)
from infra.persistence.models.portfolio_risk import PortfolioRiskSnapshotModel
from packages.contracts.identities import (
    AccountId,
    AssetClass,
    InstrumentId,
    InstrumentType,
    VenueId,
)
from packages.contracts.primitives import normalize_utc_datetime


@dataclass(frozen=True, slots=True)
class StoredPortfolioRiskSnapshot:
    snapshot_id: str
    snapshot: PortfolioRiskSnapshot
    limits: PortfolioRiskLimits
    source: str
    recorded_at: datetime


def _require_text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be non-empty")
    return value.strip()


def _serialize_exposures(snapshot: PortfolioRiskSnapshot) -> str:
    return json.dumps(
        [
            {
                "position_group_id": item.position_group_id,
                "account_venue_id": str(item.account_id.venue_id),
                "account_value": item.account_id.value,
                "instrument_venue_id": str(item.instrument_id.venue_id),
                "native_symbol": item.instrument_id.native_symbol,
                "instrument_type": item.instrument_id.instrument_type.value,
                "asset_class": item.instrument_id.asset_class.value,
                "strategy": item.strategy,
                "settlement_currency": item.settlement_currency,
                "correlation_cluster": item.correlation_cluster,
                "signed_notional": str(item.signed_notional),
                "margin_used": str(item.margin_used),
            }
            for item in snapshot.exposures
        ],
        sort_keys=True,
        separators=(",", ":"),
    )


def _serialize_limits(limits: PortfolioRiskLimits) -> str:
    return json.dumps(
        {
            "max_open_position_groups": limits.max_open_position_groups,
            "max_gross_exposure": str(limits.max_gross_exposure),
            "max_net_exposure": str(limits.max_net_exposure),
            "max_account_exposure": str(limits.max_account_exposure),
            "max_venue_exposure": str(limits.max_venue_exposure),
            "max_strategy_exposure": str(limits.max_strategy_exposure),
            "max_instrument_exposure": str(limits.max_instrument_exposure),
            "max_currency_concentration": str(limits.max_currency_concentration),
            "max_correlation_cluster_exposure": str(
                limits.max_correlation_cluster_exposure
            ),
            "max_leverage": str(limits.max_leverage),
            "max_margin_utilization": str(limits.max_margin_utilization),
            "max_daily_drawdown": str(limits.max_daily_drawdown),
            "max_rolling_drawdown": str(limits.max_rolling_drawdown),
            "max_order_liquidity_ratio": str(limits.max_order_liquidity_ratio),
            "max_expected_slippage_bps": str(limits.max_expected_slippage_bps),
            "hedge_tolerance": str(limits.hedge_tolerance),
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _snapshot_id(
    *,
    snapshot: PortfolioRiskSnapshot,
    exposures_json: str,
    limits_json: str,
    source: str,
) -> str:
    payload = json.dumps(
        {
            "user_id": snapshot.user_id,
            "observation_state": snapshot.observation_state.value,
            "trading_state": snapshot.trading_state.value,
            "equity": str(snapshot.equity),
            "daily_start_equity": str(snapshot.daily_start_equity),
            "rolling_peak_equity": str(snapshot.rolling_peak_equity),
            "exposures_json": exposures_json,
            "limits_json": limits_json,
            "source": source,
            "observed_at": snapshot.observed_at.isoformat(),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class PortfolioRiskSnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        if not isinstance(session, AsyncSession):
            raise ValueError("session must be AsyncSession")
        self._session = session

    async def append(
        self,
        *,
        snapshot: PortfolioRiskSnapshot,
        limits: PortfolioRiskLimits,
        source: str,
        recorded_at: datetime,
    ) -> str:
        if not isinstance(snapshot, PortfolioRiskSnapshot):
            raise ValueError("snapshot must be PortfolioRiskSnapshot")
        if not isinstance(limits, PortfolioRiskLimits):
            raise ValueError("limits must be PortfolioRiskLimits")
        source = _require_text(source, field_name="source")
        recorded_at = normalize_utc_datetime(
            recorded_at,
            field_name="recorded_at",
        )
        if recorded_at < snapshot.observed_at:
            raise ValueError("recorded_at must not precede observed_at")

        exposures_json = _serialize_exposures(snapshot)
        limits_json = _serialize_limits(limits)
        snapshot_id = _snapshot_id(
            snapshot=snapshot,
            exposures_json=exposures_json,
            limits_json=limits_json,
            source=source,
        )
        existing = await self._session.get(
            PortfolioRiskSnapshotModel,
            snapshot_id,
        )
        if existing is not None:
            if (
                existing.user_id == snapshot.user_id
                and existing.exposures_json == exposures_json
                and existing.limits_json == limits_json
                and existing.source == source
            ):
                return snapshot_id
            raise ValueError("immutable Portfolio Risk snapshot conflict")

        self._session.add(
            PortfolioRiskSnapshotModel(
                snapshot_id=snapshot_id,
                user_id=snapshot.user_id,
                observation_state=snapshot.observation_state.value,
                trading_state=snapshot.trading_state.value,
                equity=snapshot.equity,
                daily_start_equity=snapshot.daily_start_equity,
                rolling_peak_equity=snapshot.rolling_peak_equity,
                exposures_json=exposures_json,
                limits_json=limits_json,
                source=source,
                observed_at=snapshot.observed_at,
                recorded_at=recorded_at,
            )
        )
        return snapshot_id

    async def list_recent_for_user(
        self,
        *,
        user_id: int,
        limit: int = 100,
    ) -> tuple[StoredPortfolioRiskSnapshot, ...]:
        if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
            raise ValueError("user_id must be a positive integer")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 1000:
            raise ValueError("limit must be an integer in [1, 1000]")

        result = await self._session.execute(
            select(PortfolioRiskSnapshotModel)
            .where(PortfolioRiskSnapshotModel.user_id == user_id)
            .order_by(
                PortfolioRiskSnapshotModel.observed_at.desc(),
                PortfolioRiskSnapshotModel.snapshot_id.desc(),
            )
            .limit(limit)
        )
        return tuple(
            self._to_stored(model)
            for model in result.scalars().all()
        )

    async def latest_for_user(
        self,
        *,
        user_id: int,
    ) -> StoredPortfolioRiskSnapshot | None:
        values = await self.list_recent_for_user(user_id=user_id, limit=1)
        return None if not values else values[0]

    @staticmethod
    def _to_stored(model: PortfolioRiskSnapshotModel) -> StoredPortfolioRiskSnapshot:
        exposure_rows = json.loads(model.exposures_json)
        exposures = tuple(
            PortfolioExposure(
                position_group_id=row["position_group_id"],
                account_id=AccountId(
                    venue_id=VenueId(row["account_venue_id"]),
                    value=int(row["account_value"]),
                ),
                instrument_id=InstrumentId(
                    venue_id=VenueId(row["instrument_venue_id"]),
                    native_symbol=row["native_symbol"],
                    instrument_type=InstrumentType(row["instrument_type"]),
                    asset_class=AssetClass(row["asset_class"]),
                ),
                strategy=row["strategy"],
                settlement_currency=row["settlement_currency"],
                correlation_cluster=row["correlation_cluster"],
                signed_notional=Decimal(row["signed_notional"]),
                margin_used=Decimal(row["margin_used"]),
            )
            for row in exposure_rows
        )
        raw_limits = json.loads(model.limits_json)
        limits = PortfolioRiskLimits(
            max_open_position_groups=int(raw_limits["max_open_position_groups"]),
            max_gross_exposure=Decimal(raw_limits["max_gross_exposure"]),
            max_net_exposure=Decimal(raw_limits["max_net_exposure"]),
            max_account_exposure=Decimal(raw_limits["max_account_exposure"]),
            max_venue_exposure=Decimal(raw_limits["max_venue_exposure"]),
            max_strategy_exposure=Decimal(raw_limits["max_strategy_exposure"]),
            max_instrument_exposure=Decimal(raw_limits["max_instrument_exposure"]),
            max_currency_concentration=Decimal(raw_limits["max_currency_concentration"]),
            max_correlation_cluster_exposure=Decimal(
                raw_limits["max_correlation_cluster_exposure"]
            ),
            max_leverage=Decimal(raw_limits["max_leverage"]),
            max_margin_utilization=Decimal(raw_limits["max_margin_utilization"]),
            max_daily_drawdown=Decimal(raw_limits["max_daily_drawdown"]),
            max_rolling_drawdown=Decimal(raw_limits["max_rolling_drawdown"]),
            max_order_liquidity_ratio=Decimal(raw_limits["max_order_liquidity_ratio"]),
            max_expected_slippage_bps=Decimal(raw_limits["max_expected_slippage_bps"]),
            hedge_tolerance=Decimal(raw_limits["hedge_tolerance"]),
        )
        observed_at = model.observed_at
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=UTC)
        recorded_at = model.recorded_at
        if recorded_at.tzinfo is None:
            recorded_at = recorded_at.replace(tzinfo=UTC)
        snapshot = PortfolioRiskSnapshot(
            user_id=model.user_id,
            observation_state=RiskObservationState(model.observation_state),
            trading_state=PortfolioRiskState(model.trading_state),
            equity=Decimal(model.equity),
            daily_start_equity=Decimal(model.daily_start_equity),
            rolling_peak_equity=Decimal(model.rolling_peak_equity),
            exposures=exposures,
            observed_at=observed_at,
        )
        return StoredPortfolioRiskSnapshot(
            snapshot_id=model.snapshot_id,
            snapshot=snapshot,
            limits=limits,
            source=model.source,
            recorded_at=recorded_at,
        )
