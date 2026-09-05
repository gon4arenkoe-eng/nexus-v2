"""SQLAlchemy persistence models for canonical execution plans."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from infra.persistence.base import PersistenceBase


_METADATA_TYPE = JSON().with_variant(JSONB(), "postgresql")


class ExecutionPlanModel(PersistenceBase):
    """Durable canonical ExecutionPlan root."""

    __tablename__ = "execution_plans"
    __table_args__ = (
        CheckConstraint(
            "user_id > 0",
            name="ck_execution_plans_user_id_positive",
        ),
        CheckConstraint(
            "schema_version > 0",
            name="ck_execution_plans_schema_version_positive",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    plan_id: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
        unique=True,
    )
    intent_id: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
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
    source: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    schema_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    metadata_payload: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        _METADATA_TYPE,
        nullable=False,
        default=dict,
    )


class ExecutionPlanLegModel(PersistenceBase):
    """Immutable durable projection of one planned execution leg."""

    __tablename__ = "execution_plan_legs"
    __table_args__ = (
        UniqueConstraint(
            "plan_id",
            "leg_id",
            name="uq_execution_plan_legs_plan_leg",
        ),
        UniqueConstraint(
            "order_id",
            name="uq_execution_plan_legs_order_id",
        ),
        UniqueConstraint(
            "client_order_id",
            name="uq_execution_plan_legs_client_order_id",
        ),
        CheckConstraint(
            "account_value > 0",
            name="ck_execution_plan_legs_account_value_positive",
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_execution_plan_legs_quantity_positive",
        ),
        CheckConstraint(
            "limit_price IS NULL OR limit_price > 0",
            name="ck_execution_plan_legs_limit_price_positive",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
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

    leg_id: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )
    order_id: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )
    client_order_id: Mapped[str] = mapped_column(
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

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(38, 18),
        nullable=False,
    )

    order_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    limit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(38, 18),
        nullable=True,
    )

    reduce_only: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
