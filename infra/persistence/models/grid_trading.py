"""Persistent Grid Trading Desk checkpoints."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from infra.persistence.base import PersistenceBase


class GridInstanceStateModel(PersistenceBase):
    __tablename__ = "grid_instance_states"
    __table_args__ = (CheckConstraint("user_id > 0"),)

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    instance_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    program_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)  # noqa: E501
    account_venue_id: Mapped[str] = mapped_column(String(80), nullable=False)
    account_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    instrument_venue_id: Mapped[str] = mapped_column(String(80), nullable=False)  # noqa: E501
    instrument_symbol: Mapped[str] = mapped_column(String(160), nullable=False)
    instrument_type: Mapped[str] = mapped_column(String(32), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(32), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # noqa: E501
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # noqa: E501
