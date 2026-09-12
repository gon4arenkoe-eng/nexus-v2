"""Persistent state for single-leg execution coordination."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from infra.persistence.base import PersistenceBase


class ExecutionCoordinatorStateModel(PersistenceBase):
    """Durable coordinator checkpoint keyed by user and order."""

    __tablename__ = "execution_coordinator_states"

    __table_args__ = (
        CheckConstraint("user_id > 0"),
        CheckConstraint("account_value > 0"),
        CheckConstraint("attempt >= 0"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )
    order_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey(
            "execution_orders.order_id",
            ondelete="RESTRICT",
        ),
        primary_key=True,
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
    state: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )
    attempt: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    venue_order_id: Mapped[str | None] = mapped_column(
        String(160),
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
