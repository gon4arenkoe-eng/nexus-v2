"""Canonical evidence-bound AIEA model/strategy registry."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Mapping

from apps.aiea.domain.research import (
    ArtifactKind,
    CandidateVersion,
    PromotionReadiness,
    ResearchArtifact,
)
from apps.aiea.ports.research import ResearchRecordStore


REGISTRY_SCHEMA_VERSION = "nexus.aiea.model-registry.v1"


class ModelRegistryError(ValueError):
    """Registry metadata is incomplete or inconsistent."""


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    workspace_id: str
    user_id: int
    candidate_id: str
    strategy_id: str
    version: str
    parent_version: str | None
    dataset_id: str
    dataset_version: str
    dataset_hash: str
    feature_definition_hash: str
    model_hash: str
    code_hash: str
    hyperparameters: Mapping[str, object]
    train_interval: str
    validation_interval: str
    test_interval: str
    cost_model_version: str
    result_hash: str
    evidence_hashes: tuple[str, ...]
    environment_digest: str
    promotion_status: str
    rollback_target: str
    created_at: datetime

    def __post_init__(self) -> None:
        required = (
            "workspace_id",
            "candidate_id",
            "strategy_id",
            "version",
            "dataset_id",
            "dataset_version",
            "dataset_hash",
            "feature_definition_hash",
            "model_hash",
            "code_hash",
            "train_interval",
            "validation_interval",
            "test_interval",
            "cost_model_version",
            "result_hash",
            "environment_digest",
            "promotion_status",
            "rollback_target",
        )
        for name in required:
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ModelRegistryError(f"{name} must be non-empty")
        if self.user_id <= 0:
            raise ModelRegistryError("user_id must be positive")
        if self.parent_version == self.version:
            raise ModelRegistryError("parent_version must differ from version")
        if not self.evidence_hashes:
            raise ModelRegistryError("evidence_hashes must be non-empty")
        if len(self.evidence_hashes) != len(set(self.evidence_hashes)):
            raise ModelRegistryError("evidence_hashes must be unique")
        if not isinstance(self.hyperparameters, Mapping):
            raise ModelRegistryError("hyperparameters must be a mapping")
        if not isinstance(self.created_at, datetime):
            raise ModelRegistryError("created_at must be datetime")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ModelRegistryError("created_at must be timezone-aware")
        object.__setattr__(
            self,
            "hyperparameters",
            MappingProxyType(dict(self.hyperparameters)),
        )


class ModelRegistryService:
    """Build registry metadata without granting activation authority."""

    @staticmethod
    def build(
        *,
        candidate: CandidateVersion,
        readiness: PromotionReadiness,
        model_hash: str,
        hyperparameters: Mapping[str, object],
        result_hash: str,
    ) -> RegistryEntry:
        if (
            readiness.workspace_id != candidate.workspace_id
            or readiness.user_id != candidate.user_id
        ):
            raise ModelRegistryError("cross-tenant readiness is forbidden")
        if readiness.candidate_id != candidate.candidate_id:
            raise ModelRegistryError("candidate/readiness mismatch")
        if readiness.strategy_id != candidate.strategy_id:
            raise ModelRegistryError("strategy/readiness mismatch")
        if readiness.candidate_version != candidate.version:
            raise ModelRegistryError("candidate version/readiness mismatch")
        if readiness.dataset_hash != candidate.dataset.content_hash:
            raise ModelRegistryError("dataset lineage/readiness mismatch")
        if readiness.code_hash != candidate.code_hash:
            raise ModelRegistryError("code lineage/readiness mismatch")
        if readiness.environment_digest != candidate.environment_digest:
            raise ModelRegistryError("environment lineage/readiness mismatch")

        return RegistryEntry(
            workspace_id=candidate.workspace_id,
            user_id=candidate.user_id,
            candidate_id=candidate.candidate_id,
            strategy_id=candidate.strategy_id,
            version=candidate.version,
            parent_version=candidate.parent_version,
            dataset_id=candidate.dataset.dataset_id,
            dataset_version=candidate.dataset.version,
            dataset_hash=candidate.dataset.content_hash,
            feature_definition_hash=candidate.dataset.feature_definition_hash,
            model_hash=model_hash,
            code_hash=candidate.code_hash,
            hyperparameters=hyperparameters,
            train_interval=candidate.dataset.train_interval,
            validation_interval=candidate.dataset.validation_interval,
            test_interval=candidate.dataset.test_interval,
            cost_model_version=candidate.cost_model_version,
            result_hash=result_hash,
            evidence_hashes=readiness.evidence_hashes,
            environment_digest=candidate.environment_digest,
            promotion_status=readiness.state.value,
            rollback_target=readiness.rollback_version,
            created_at=candidate.created_at,
        )

    @staticmethod
    def artifact_id(*, strategy_id: str, version: str) -> str:
        strategy = strategy_id.strip()
        candidate_version = version.strip()
        if not strategy or not candidate_version:
            raise ModelRegistryError("strategy_id and version must be non-empty")
        return f"model:{strategy}:{candidate_version}"

    @staticmethod
    def to_artifact(entry: RegistryEntry) -> ResearchArtifact:
        parent_artifact_id = None
        if entry.parent_version is not None:
            parent_artifact_id = ModelRegistryService.artifact_id(
                strategy_id=entry.strategy_id,
                version=entry.parent_version,
            )
        return ResearchArtifact(
            artifact_id=ModelRegistryService.artifact_id(
                strategy_id=entry.strategy_id,
                version=entry.version,
            ),
            workspace_id=entry.workspace_id,
            user_id=entry.user_id,
            kind=ArtifactKind.MODEL,
            version=entry.version,
            content_hash=entry.model_hash,
            parent_artifact_id=parent_artifact_id,
            created_at=entry.created_at,
            metadata={
                "registry_schema": REGISTRY_SCHEMA_VERSION,
                "candidate_id": entry.candidate_id,
                "strategy_id": entry.strategy_id,
                "parent_version": entry.parent_version,
                "dataset_id": entry.dataset_id,
                "dataset_version": entry.dataset_version,
                "dataset_hash": entry.dataset_hash,
                "feature_definition_hash": entry.feature_definition_hash,
                "code_hash": entry.code_hash,
                "hyperparameters": dict(entry.hyperparameters),
                "train_interval": entry.train_interval,
                "validation_interval": entry.validation_interval,
                "test_interval": entry.test_interval,
                "cost_model_version": entry.cost_model_version,
                "result_hash": entry.result_hash,
                "evidence_hashes": list(entry.evidence_hashes),
                "environment_digest": entry.environment_digest,
                "promotion_status": entry.promotion_status,
                "rollback_target": entry.rollback_target,
            },
        )

    @staticmethod
    def from_artifact(artifact: ResearchArtifact) -> RegistryEntry:
        if artifact.kind is not ArtifactKind.MODEL:
            raise ModelRegistryError("registry artifact must be MODEL")
        metadata = artifact.metadata
        if metadata.get("registry_schema") != REGISTRY_SCHEMA_VERSION:
            raise ModelRegistryError("unsupported model registry artifact schema")

        hyperparameters = metadata.get("hyperparameters")
        if not isinstance(hyperparameters, Mapping):
            raise ModelRegistryError("registry artifact hyperparameters are invalid")
        evidence_hashes = metadata.get("evidence_hashes")
        if not isinstance(evidence_hashes, (list, tuple)):
            raise ModelRegistryError("registry artifact evidence_hashes are invalid")

        def text(name: str) -> str:
            value = metadata.get(name)
            if not isinstance(value, str) or not value.strip():
                raise ModelRegistryError(f"registry artifact {name} is invalid")
            return value

        parent_version_value = metadata.get("parent_version")
        parent_version = None
        if parent_version_value is not None:
            if not isinstance(parent_version_value, str) or not parent_version_value.strip():
                raise ModelRegistryError("registry artifact parent_version is invalid")
            parent_version = parent_version_value

        return RegistryEntry(
            workspace_id=artifact.workspace_id,
            user_id=artifact.user_id,
            candidate_id=text("candidate_id"),
            strategy_id=text("strategy_id"),
            version=artifact.version,
            parent_version=parent_version,
            dataset_id=text("dataset_id"),
            dataset_version=text("dataset_version"),
            dataset_hash=text("dataset_hash"),
            feature_definition_hash=text("feature_definition_hash"),
            model_hash=artifact.content_hash,
            code_hash=text("code_hash"),
            hyperparameters={str(key): value for key, value in hyperparameters.items()},
            train_interval=text("train_interval"),
            validation_interval=text("validation_interval"),
            test_interval=text("test_interval"),
            cost_model_version=text("cost_model_version"),
            result_hash=text("result_hash"),
            evidence_hashes=tuple(str(item) for item in evidence_hashes),
            environment_digest=text("environment_digest"),
            promotion_status=text("promotion_status"),
            rollback_target=text("rollback_target"),
            created_at=artifact.created_at,
        )


class DurableModelRegistry:
    """Restart-safe model registry backed by the canonical AIEA research store."""

    def __init__(self, store: ResearchRecordStore) -> None:
        self._store = store

    async def register(self, entry: RegistryEntry) -> ResearchArtifact:
        artifact = ModelRegistryService.to_artifact(entry)
        await self._store.append_artifact(artifact)
        return artifact

    async def get(
        self,
        *,
        workspace_id: str,
        user_id: int,
        strategy_id: str,
        version: str,
    ) -> RegistryEntry | None:
        artifact = await self._store.get_artifact(
            workspace_id=workspace_id,
            user_id=user_id,
            kind=ArtifactKind.MODEL,
            artifact_id=ModelRegistryService.artifact_id(
                strategy_id=strategy_id,
                version=version,
            ),
        )
        if artifact is None:
            return None
        return ModelRegistryService.from_artifact(artifact)

    async def list_for_owner(
        self,
        *,
        workspace_id: str,
        user_id: int,
    ) -> tuple[RegistryEntry, ...]:
        artifacts = await self._store.list_artifacts_for_owner(
            workspace_id=workspace_id,
            user_id=user_id,
            kind=ArtifactKind.MODEL,
        )
        values: list[RegistryEntry] = []
        for artifact in artifacts:
            if artifact.metadata.get("registry_schema") != REGISTRY_SCHEMA_VERSION:
                continue
            values.append(ModelRegistryService.from_artifact(artifact))
        return tuple(sorted(values, key=lambda item: (item.strategy_id, item.version)))
