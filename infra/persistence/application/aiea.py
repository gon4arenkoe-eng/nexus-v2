"""Persistence adapter for canonical AIEA research records."""

from __future__ import annotations

from collections.abc import Mapping

from dataclasses import fields, is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from apps.aiea.domain.research import (
    CandidateVersion,
    ExperimentRecord,
    Hypothesis,
    KnowledgeSnapshot,
    ResearchArtifact,
    ResearchEvidence,
    ResearchMemoryEntry,
)
from infra.persistence.repositories.aiea import (
    AIEAResearchRecordRepository,
    AIEAStoredRecord,
)


def _json_value(value: Any) -> Any:
    if is_dataclass(value):
        return {
            field.name: _json_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_value(item) for item in value]
    return value


def _serialize(value: object) -> str:
    return json.dumps(
        _json_value(value),
        sort_keys=True,
        separators=(",", ":"),
    )


def _hash(payload: str) -> str:
    return sha256(payload.encode("utf-8")).hexdigest()


class AIEAResearchRecordStore:
    def __init__(self, repository: AIEAResearchRecordRepository) -> None:
        self._repository = repository

    async def append_snapshot(self, value: KnowledgeSnapshot) -> None:
        await self._append(
            value,
            record_type="snapshot",
            record_id=value.snapshot_id,
            workspace_id=value.workspace_id,
            user_id=value.user_id,
            created_at=value.created_at,
        )

    async def append_evidence(self, value: ResearchEvidence) -> None:
        await self._append(
            value,
            record_type="evidence",
            record_id=value.evidence_id,
            workspace_id=value.workspace_id,
            user_id=value.user_id,
            created_at=value.observed_at,
        )

    async def append_memory(self, value: ResearchMemoryEntry) -> None:
        await self._append(
            value,
            record_type="memory",
            record_id=value.memory_id,
            workspace_id=value.workspace_id,
            user_id=value.user_id,
            created_at=value.created_at,
            parent_record_id=value.parent_memory_id,
        )

    async def append_hypothesis(self, value: Hypothesis) -> None:
        await self._append(
            value,
            record_type="hypothesis",
            record_id=value.hypothesis_id,
            workspace_id=value.workspace_id,
            user_id=value.user_id,
            created_at=value.created_at,
            parent_record_id=value.snapshot_id,
        )

    async def append_candidate(self, value: CandidateVersion) -> None:
        await self._append(
            value,
            record_type="candidate",
            record_id=value.candidate_id,
            workspace_id=value.workspace_id,
            user_id=value.user_id,
            created_at=value.created_at,
            parent_record_id=value.parent_version,
        )

    async def append_experiment(self, value: ExperimentRecord) -> None:
        await self._append(
            value,
            record_type="experiment",
            record_id=value.experiment_id,
            workspace_id=value.workspace_id,
            user_id=value.user_id,
            created_at=value.completed_at,
            parent_record_id=value.candidate_id,
        )

    async def append_artifact(self, value: ResearchArtifact) -> None:
        await self._append(
            value,
            record_type=f"artifact:{value.kind.value.lower()}",
            record_id=value.artifact_id,
            workspace_id=value.workspace_id,
            user_id=value.user_id,
            created_at=value.created_at,
            parent_record_id=value.parent_artifact_id,
        )

    async def list_record_ids(
        self,
        *,
        workspace_id: str,
        user_id: int,
    ) -> tuple[str, ...]:
        records = await self._repository.list_for_owner(
            workspace_id=workspace_id,
            user_id=user_id,
        )
        return tuple(record.record_id for record in records)

    async def _append(
        self,
        value: object,
        *,
        record_type: str,
        record_id: str,
        workspace_id: str,
        user_id: int,
        created_at: datetime,
        parent_record_id: str | None = None,
    ) -> None:
        payload = _serialize(value)
        await self._repository.append(
            AIEAStoredRecord(
                workspace_id=workspace_id,
                user_id=user_id,
                record_type=record_type,
                record_id=record_id,
                parent_record_id=parent_record_id,
                content_hash=_hash(payload),
                payload_json=payload,
                created_at=created_at,
            )
        )
