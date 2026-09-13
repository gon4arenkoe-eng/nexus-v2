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
    ArtifactKind,
    CandidateVersion,
    ExperimentRecord,
    ExperimentStage,
    FalsificationCheck,
    Hypothesis,
    KnowledgeSnapshot,
    ResearchArtifact,
    ResearchEvidence,
    ResearchMemoryEntry,
    ValidationOutcome,
    ValidationResult,
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


def _load(payload_json: str) -> dict[str, Any]:
    value = json.loads(payload_json)
    if not isinstance(value, dict):
        raise ValueError("AIEA payload must be an object")
    return value


def _validation_result(value: Mapping[str, Any]) -> ValidationResult:
    return ValidationResult(
        check=FalsificationCheck(str(value["check"])),
        outcome=ValidationOutcome(str(value["outcome"])),
        score=Decimal(str(value["score"])),
        evidence_hash=str(value["evidence_hash"]),
        detail=str(value["detail"]),
    )


def _artifact(payload_json: str) -> ResearchArtifact:
    value = _load(payload_json)
    metadata = value.get("metadata", {})
    if not isinstance(metadata, Mapping):
        raise ValueError("artifact metadata payload is invalid")
    parent = value.get("parent_artifact_id")
    return ResearchArtifact(
        artifact_id=str(value["artifact_id"]),
        workspace_id=str(value["workspace_id"]),
        user_id=int(value["user_id"]),
        kind=ArtifactKind(str(value["kind"])),
        version=str(value["version"]),
        content_hash=str(value["content_hash"]),
        parent_artifact_id=None if parent is None else str(parent),
        created_at=datetime.fromisoformat(str(value["created_at"])),
        metadata={str(key): item for key, item in metadata.items()},
    )


def _experiment(payload_json: str) -> ExperimentRecord:
    value = _load(payload_json)
    metrics = value.get("metrics", {})
    if not isinstance(metrics, Mapping):
        raise ValueError("experiment metrics payload is invalid")
    return ExperimentRecord(
        experiment_id=str(value["experiment_id"]),
        workspace_id=str(value["workspace_id"]),
        user_id=int(value["user_id"]),
        hypothesis_id=str(value["hypothesis_id"]),
        candidate_id=str(value["candidate_id"]),
        stage=ExperimentStage(str(value["stage"])),
        started_at=datetime.fromisoformat(str(value["started_at"])),
        completed_at=datetime.fromisoformat(str(value["completed_at"])),
        dataset_hash=str(value["dataset_hash"]),
        code_hash=str(value["code_hash"]),
        environment_digest=str(value["environment_digest"]),
        cost_model_version=str(value["cost_model_version"]),
        results=tuple(_validation_result(item) for item in value["results"]),
        metrics={str(key): Decimal(str(item)) for key, item in metrics.items()},
    )


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

    async def get_artifact(
        self,
        *,
        workspace_id: str,
        user_id: int,
        kind: ArtifactKind,
        artifact_id: str,
    ) -> ResearchArtifact | None:
        record = await self._repository.get(
            workspace_id=workspace_id,
            user_id=user_id,
            record_type=f"artifact:{kind.value.lower()}",
            record_id=artifact_id,
        )
        return None if record is None else _artifact(record.payload_json)

    async def list_artifacts_for_owner(
        self,
        *,
        workspace_id: str,
        user_id: int,
        kind: ArtifactKind | None = None,
    ) -> tuple[ResearchArtifact, ...]:
        records = await self._repository.list_for_owner(
            workspace_id=workspace_id,
            user_id=user_id,
        )
        record_type = None if kind is None else f"artifact:{kind.value.lower()}"
        values = tuple(
            _artifact(record.payload_json)
            for record in records
            if record.record_type.startswith("artifact:")
            and (record_type is None or record.record_type == record_type)
        )
        return tuple(
            sorted(
                values,
                key=lambda item: (item.kind.value, item.artifact_id, item.version),
            )
        )

    async def list_experiments_for_candidate(
        self,
        *,
        workspace_id: str,
        user_id: int,
        candidate_id: str,
    ) -> tuple[ExperimentRecord, ...]:
        records = await self._repository.list_children(
            workspace_id=workspace_id,
            user_id=user_id,
            record_type="experiment",
            parent_record_id=candidate_id,
        )
        return tuple(_experiment(record.payload_json) for record in records)

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
