"""Tenant-scoped repository for immutable AIEA research records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infra.persistence.models.aiea import AIEAResearchRecordModel


@dataclass(frozen=True, slots=True)
class AIEAStoredRecord:
    workspace_id: str
    user_id: int
    record_type: str
    record_id: str
    parent_record_id: str | None
    content_hash: str
    payload_json: str
    created_at: datetime


class AIEAResearchRecordRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, record: AIEAStoredRecord) -> None:
        existing = await self._session.get(
            AIEAResearchRecordModel,
            (
                record.workspace_id,
                record.user_id,
                record.record_type,
                record.record_id,
            ),
        )
        if existing is not None:
            if (
                existing.content_hash == record.content_hash
                and existing.payload_json == record.payload_json
                and existing.parent_record_id == record.parent_record_id
            ):
                return
            raise ValueError("immutable AIEA research record conflict")
        self._session.add(
            AIEAResearchRecordModel(
                workspace_id=record.workspace_id,
                user_id=record.user_id,
                record_type=record.record_type,
                record_id=record.record_id,
                parent_record_id=record.parent_record_id,
                content_hash=record.content_hash,
                payload_json=record.payload_json,
                created_at=record.created_at,
            )
        )

    async def get(
        self,
        *,
        workspace_id: str,
        user_id: int,
        record_type: str,
        record_id: str,
    ) -> AIEAStoredRecord | None:
        model = await self._session.get(
            AIEAResearchRecordModel,
            (workspace_id, user_id, record_type, record_id),
        )
        return None if model is None else self._to_record(model)


    async def list_children(
        self,
        *,
        workspace_id: str,
        user_id: int,
        record_type: str,
        parent_record_id: str,
    ) -> tuple[AIEAStoredRecord, ...]:
        result = await self._session.execute(
            select(AIEAResearchRecordModel)
            .where(
                AIEAResearchRecordModel.workspace_id == workspace_id,
                AIEAResearchRecordModel.user_id == user_id,
                AIEAResearchRecordModel.record_type == record_type,
                AIEAResearchRecordModel.parent_record_id == parent_record_id,
            )
            .order_by(
                AIEAResearchRecordModel.created_at,
                AIEAResearchRecordModel.record_id,
            )
        )
        return tuple(self._to_record(model) for model in result.scalars().all())

    async def list_for_owner(
        self,
        *,
        workspace_id: str,
        user_id: int,
    ) -> tuple[AIEAStoredRecord, ...]:
        result = await self._session.execute(
            select(AIEAResearchRecordModel)
            .where(
                AIEAResearchRecordModel.workspace_id == workspace_id,
                AIEAResearchRecordModel.user_id == user_id,
            )
            .order_by(
                AIEAResearchRecordModel.created_at,
                AIEAResearchRecordModel.record_type,
                AIEAResearchRecordModel.record_id,
            )
        )
        return tuple(self._to_record(model) for model in result.scalars().all())  # noqa: E501

    @staticmethod
    def _to_record(model: AIEAResearchRecordModel) -> AIEAStoredRecord:
        created_at = model.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        return AIEAStoredRecord(
            workspace_id=model.workspace_id,
            user_id=model.user_id,
            record_type=model.record_type,
            record_id=model.record_id,
            parent_record_id=model.parent_record_id,
            content_hash=model.content_hash,
            payload_json=model.payload_json,
            created_at=created_at,
        )
