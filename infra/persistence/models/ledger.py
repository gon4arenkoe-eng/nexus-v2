"""SQLAlchemy persistence model for immutable execution Ledger events."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from infra.persistence.base import PersistenceBase


_PAYLOAD_TYPE = JSON().with_variant(JSONB(), "postgresql")


class ExecutionLedgerEventModel(PersistenceBase):
    """Immutable durable evidence for one canonical execution Ledger event."""

    __tablename__ = "execution_ledger_events"
    __table_args__ = (
        UniqueConstraint(
            "event_id",
            name="uq_execution_ledger_events_event_id",
        ),
        ForeignKeyConstraint(
            ["group_id", "leg_id"],
            ["position_legs.group_id", "position_legs.leg_id"],
            name="fk_execution_ledger_events_position_leg",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "event_version > 0",
            name="ck_execution_ledger_events_event_version_positive",
        ),
        CheckConstraint(
            "user_id > 0",
            name="ck_execution_ledger_events_user_id_positive",
        ),
        CheckConstraint(
            "account_value IS NULL OR account_value > 0",
            name="ck_execution_ledger_events_account_value_positive",
        ),
        CheckConstraint(
            "schema_version > 0",
            name="ck_execution_ledger_events_schema_version_positive",
        ),
        CheckConstraint(
            "account_value IS NULL OR venue_id IS NOT NULL",
            name="ck_execution_ledger_events_account_requires_venue",
        ),
        CheckConstraint(
            "instrument_venue_id IS NULL OR "
            "venue_id IS NULL OR instrument_venue_id = venue_id",
            name="ck_execution_ledger_events_matching_venue",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    event_id: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        index=True,
    )

    event_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    plan_id: Mapped[str | None] = mapped_column(
        String(160),
        ForeignKey(
            "execution_plans.plan_id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    group_id: Mapped[str | None] = mapped_column(
        String(160),
        ForeignKey(
            "position_groups.group_id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    leg_id: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
        index=True,
    )

    order_id: Mapped[str | None] = mapped_column(
        String(160),
        ForeignKey(
            "execution_orders.order_id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    fill_id: Mapped[str | None] = mapped_column(
        String(160),
        ForeignKey(
            "execution_fills.fill_id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    venue_id: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
        index=True,
    )

    account_value: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    instrument_venue_id: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    native_symbol: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
    )

    instrument_type: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    asset_class: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    correlation_id: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
        index=True,
    )

    causation_id: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
        index=True,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    sequence_no: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    evidence_source: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
    )

    evidence_quality: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    schema_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    payload: Mapped[dict[str, Any]] = mapped_column(
        _PAYLOAD_TYPE,
        nullable=False,
        default=dict,
        server_default=text("'{}'"),
    )
