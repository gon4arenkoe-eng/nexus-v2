"""AIEA ports for durable research records and isolated research workers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from apps.aiea.domain.research import (
    ArtifactKind,
    CandidateVersion,
    ExperimentRecord,
    Hypothesis,
    KnowledgeSnapshot,
    ResearchArtifact,
    ResearchEvidence,
    ResearchMemoryEntry,
)


if TYPE_CHECKING:
    from apps.aiea.application.research_loop import ResearchTask


class ResearchRecordStore(Protocol):
    async def append_snapshot(self, value: KnowledgeSnapshot) -> None: ...

    async def append_evidence(self, value: ResearchEvidence) -> None: ...

    async def append_memory(self, value: ResearchMemoryEntry) -> None: ...

    async def append_hypothesis(self, value: Hypothesis) -> None: ...

    async def append_candidate(self, value: CandidateVersion) -> None: ...

    async def append_experiment(self, value: ExperimentRecord) -> None: ...

    async def append_artifact(self, value: ResearchArtifact) -> None: ...

    async def get_artifact(
        self,
        *,
        workspace_id: str,
        user_id: int,
        kind: ArtifactKind,
        artifact_id: str,
    ) -> ResearchArtifact | None: ...

    async def list_artifacts_for_owner(
        self,
        *,
        workspace_id: str,
        user_id: int,
        kind: ArtifactKind | None = None,
    ) -> tuple[ResearchArtifact, ...]: ...

    async def list_experiments_for_candidate(
        self,
        *,
        workspace_id: str,
        user_id: int,
        candidate_id: str,
    ) -> tuple[ExperimentRecord, ...]: ...

    async def list_record_ids(
        self,
        *,
        workspace_id: str,
        user_id: int,
    ) -> tuple[str, ...]: ...


class ResearchWorkerPort(Protocol):
    async def execute(self, task: ResearchTask) -> ExperimentRecord: ...
