"""Persistent pair/basket execution coordinator checkpoints."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from infra.persistence.base import PersistenceBase


class MultiLegExecutionStateModel(PersistenceBase):
    __tablename__ = "multi_leg_execution_states"

    __table_args__ = (
        CheckConstraint("user_id > 0"),
    )

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    plan_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("execution_plans.plan_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    group_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("position_groups.group_id", ondelete="RESTRICT"),
        nullable=False,
    )
    shape: Mapped[str] = mapped_column(String(32), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    recovery_policy: Mapped[str] = mapped_column(String(40), nullable=False)
    legs_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
