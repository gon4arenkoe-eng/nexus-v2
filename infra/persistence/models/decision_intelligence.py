"""Immutable Decision Intelligence persistence journal."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from infra.persistence.base import PersistenceBase


class DecisionIntelligenceRecordModel(PersistenceBase):
    __tablename__ = "decision_intelligence_records"
    __table_args__ = (CheckConstraint("user_id > 0"),)

    workspace_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    record_type: Mapped[str] = mapped_column(String(32), primary_key=True)
    record_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    parent_record_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
