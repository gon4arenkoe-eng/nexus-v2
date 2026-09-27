"""Immutable canonical Portfolio Risk snapshot history."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from infra.persistence.base import PersistenceBase


class PortfolioRiskSnapshotModel(PersistenceBase):
    """One immutable PortfolioRiskSnapshot plus the limits used with it."""

    __tablename__ = "portfolio_risk_snapshots"
    __table_args__ = (
        CheckConstraint(
            "user_id > 0",
            name="ck_portfolio_risk_snapshots_user_positive",
        ),
        CheckConstraint(
            "equity > 0",
            name="ck_portfolio_risk_snapshots_equity_positive",
        ),
        CheckConstraint(
            "daily_start_equity > 0",
            name="ck_portfolio_risk_snapshots_daily_equity_positive",
        ),
        CheckConstraint(
            "rolling_peak_equity > 0",
            name="ck_portfolio_risk_snapshots_peak_equity_positive",
        ),
        Index(
            "ix_portfolio_risk_snapshots_user_observed",
            "user_id",
            "observed_at",
        ),
    )

    snapshot_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    observation_state: Mapped[str] = mapped_column(String(32), nullable=False)
    trading_state: Mapped[str] = mapped_column(String(32), nullable=False)
    equity: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    daily_start_equity: Mapped[Decimal] = mapped_column(
        Numeric(38, 18), nullable=False
    )
    rolling_peak_equity: Mapped[Decimal] = mapped_column(
        Numeric(38, 18), nullable=False
    )
    exposures_json: Mapped[str] = mapped_column(Text, nullable=False)
    limits_json: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(160), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
