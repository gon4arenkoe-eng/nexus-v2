"""SQLAlchemy persistence models for canonical position projections."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from infra.persistence.base import PersistenceBase


class PositionGroupModel(PersistenceBase):
    """Materialized current state for one canonical position group."""

    __tablename__ = "position_groups"
    __table_args__ = (
        CheckConstraint(
            "user_id > 0",
            name="ck_position_groups_user_id_positive",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    group_id: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
        unique=True,
    )

    plan_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey(
            "execution_plans.plan_id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    shape: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    strategy: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    strategy_version: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
    )

    trade_source: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    opened_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class PositionLegModel(PersistenceBase):
    """Materialized current state for one canonical position leg."""

    __tablename__ = "position_legs"
    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "leg_id",
            name="uq_position_legs_group_leg",
        ),
        CheckConstraint(
            "account_value > 0",
            name="ck_position_legs_account_value_positive",
        ),
        CheckConstraint(
            "venue_id = instrument_venue_id",
            name="ck_position_legs_matching_venue",
        ),
        CheckConstraint(
            "target_quantity > 0",
            name="ck_position_legs_target_quantity_positive",
        ),
        CheckConstraint(
            "filled_quantity >= 0",
            name="ck_position_legs_filled_quantity_non_negative",
        ),
        CheckConstraint(
            "current_quantity >= 0",
            name="ck_position_legs_current_quantity_non_negative",
        ),
        CheckConstraint(
            "average_entry_price IS NULL OR average_entry_price > 0",
            name="ck_position_legs_average_entry_price_positive",
        ),
        CheckConstraint(
            "average_exit_price IS NULL OR average_exit_price > 0",
            name="ck_position_legs_average_exit_price_positive",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    group_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey(
            "position_groups.group_id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    leg_id: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    venue_id: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    account_value: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    instrument_venue_id: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    native_symbol: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    instrument_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    asset_class: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    side: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    target_quantity: Mapped[Decimal] = mapped_column(
        Numeric(38, 18),
        nullable=False,
    )

    filled_quantity: Mapped[Decimal] = mapped_column(
        Numeric(38, 18),
        nullable=False,
    )

    current_quantity: Mapped[Decimal] = mapped_column(
        Numeric(38, 18),
        nullable=False,
    )

    average_entry_price: Mapped[Decimal | None] = mapped_column(
        Numeric(38, 18),
        nullable=True,
    )

    average_exit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(38, 18),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    opened_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
