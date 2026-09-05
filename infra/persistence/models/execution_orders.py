"""SQLAlchemy persistence models for execution orders and fills."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from infra.persistence.base import PersistenceBase


class ExecutionOrderModel(PersistenceBase):
    """Materialized local order state plus last-known venue observation."""

    __tablename__ = "execution_orders"
    __table_args__ = (
        UniqueConstraint(
            "order_id",
            name="uq_execution_orders_order_id",
        ),
        UniqueConstraint(
            "client_order_id",
            name="uq_execution_orders_client_order_id",
        ),
        ForeignKeyConstraint(
            ["group_id", "leg_id"],
            ["position_legs.group_id", "position_legs.leg_id"],
            name="fk_execution_orders_position_leg",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "user_id > 0",
            name="ck_execution_orders_user_id_positive",
        ),
        CheckConstraint(
            "account_value > 0",
            name="ck_execution_orders_account_value_positive",
        ),
        CheckConstraint(
            "venue_id = instrument_venue_id",
            name="ck_execution_orders_matching_venue",
        ),
        CheckConstraint(
            "requested_quantity > 0",
            name="ck_execution_orders_requested_quantity_positive",
        ),
        CheckConstraint(
            "filled_quantity >= 0",
            name="ck_execution_orders_filled_quantity_non_negative",
        ),
        CheckConstraint(
            "filled_quantity <= requested_quantity",
            name="ck_execution_orders_filled_not_above_requested",
        ),
        CheckConstraint(
            "average_fill_price IS NULL OR average_fill_price > 0",
            name="ck_execution_orders_average_fill_price_positive",
        ),
        CheckConstraint(
            "limit_price IS NULL OR limit_price > 0",
            name="ck_execution_orders_limit_price_positive",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    order_id: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
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

    group_id: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
        index=True,
    )

    leg_id: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
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

    client_order_id: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    venue_order_id: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
    )

    side: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    order_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    reduce_only: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    requested_quantity: Mapped[Decimal] = mapped_column(
        Numeric(38, 18),
        nullable=False,
    )

    filled_quantity: Mapped[Decimal] = mapped_column(
        Numeric(38, 18),
        nullable=False,
    )

    average_fill_price: Mapped[Decimal | None] = mapped_column(
        Numeric(38, 18),
        nullable=True,
    )

    limit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(38, 18),
        nullable=True,
    )

    local_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    last_venue_status: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    last_venue_observed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    venue_observation_source: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    filled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
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


class ExecutionFillModel(PersistenceBase):
    """Immutable fill-evidence persistence shape."""

    __tablename__ = "execution_fills"
    __table_args__ = (
        UniqueConstraint(
            "fill_id",
            name="uq_execution_fills_fill_id",
        ),
        UniqueConstraint(
            "venue_id",
            "account_value",
            "venue_fill_id",
            name="uq_execution_fills_venue_account_fill",
        ),
        CheckConstraint(
            "user_id > 0",
            name="ck_execution_fills_user_id_positive",
        ),
        CheckConstraint(
            "account_value > 0",
            name="ck_execution_fills_account_value_positive",
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_execution_fills_quantity_positive",
        ),
        CheckConstraint(
            "price > 0",
            name="ck_execution_fills_price_positive",
        ),
        CheckConstraint(
            "fee >= 0",
            name="ck_execution_fills_fee_non_negative",
        ),
        CheckConstraint(
            "fee = 0 OR fee_currency IS NOT NULL",
            name="ck_execution_fills_positive_fee_currency",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    fill_id: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    order_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey(
            "execution_orders.order_id",
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

    venue_id: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    account_value: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    venue_fill_id: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(38, 18),
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(38, 18),
        nullable=False,
    )

    fee: Mapped[Decimal] = mapped_column(
        Numeric(38, 18),
        nullable=False,
    )

    fee_currency: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    raw_evidence_hash: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
    )
