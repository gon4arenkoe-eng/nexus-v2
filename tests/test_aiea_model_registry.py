from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from apps.aiea.application.model_registry import (
    DurableModelRegistry,
    ModelRegistryError,
    ModelRegistryService,
)
from apps.aiea.domain.research import (
    ArtifactKind,
    CandidateVersion,
    DatasetLineage,
    PromotionReadiness,
    PromotionReadinessState,
    ResearchArtifact,
)


NOW = datetime(2026, 9, 13, 21, 0, tzinfo=UTC)


def _candidate(
    *,
    workspace_id: str = "ws-1",
    user_id: int = 7,
) -> CandidateVersion:
    return CandidateVersion(
        candidate_id="cand-1",
        workspace_id=workspace_id,
        user_id=user_id,
        hypothesis_id="hyp-1",
        strategy_id="trend-v2",
        version="2.1.0",
        parent_version="2.0.0",
        before_spec_hash="before-hash",
        after_spec_hash="after-hash",
        reason="bounded research improvement",
        expected_effect="better stability",
        code_hash="code-hash",
        environment_digest="sha256:research-image",
        cost_model_version="cost-v2",
        dataset=DatasetLineage(
            dataset_id="btc-1m",
            version="v3",
            content_hash="dataset-hash",
            feature_definition_hash="feature-hash",
            train_interval="2024",
            validation_interval="2025-H1",
            test_interval="2025-H2",
        ),
        created_at=NOW,
    )


def _readiness(
    *,
    workspace_id: str = "ws-1",
    user_id: int = 7,
) -> PromotionReadiness:
    return PromotionReadiness(
        readiness_id="ready-1",
        workspace_id=workspace_id,
        user_id=user_id,
        strategy_id="trend-v2",
        candidate_version="2.1.0",
        candidate_id="cand-1",
        dataset_hash="dataset-hash",
        code_hash="code-hash",
        environment_digest="sha256:research-image",
        evidence_hashes=("evidence-a", "evidence-b"),
        rollback_version="2.0.0",
        state=PromotionReadinessState.SHADOW_READY,
    )


def _entry():
    return ModelRegistryService.build(
        candidate=_candidate(),
        readiness=_readiness(),
        model_hash="model-hash",
        hyperparameters={"lookback": 20, "threshold": "0.5"},
        result_hash="result-hash",
    )


def test_registry_entry_binds_required_research_identity() -> None:
    entry = _entry()

    assert entry.workspace_id == "ws-1"
    assert entry.user_id == 7
    assert entry.parent_version == "2.0.0"
    assert entry.dataset_version == "v3"
    assert entry.dataset_hash == "dataset-hash"
    assert entry.feature_definition_hash == "feature-hash"
    assert entry.model_hash == "model-hash"
    assert entry.code_hash == "code-hash"
    assert entry.train_interval == "2024"
    assert entry.validation_interval == "2025-H1"
    assert entry.test_interval == "2025-H2"
    assert entry.cost_model_version == "cost-v2"
    assert entry.result_hash == "result-hash"
    assert entry.evidence_hashes == ("evidence-a", "evidence-b")
    assert entry.environment_digest == "sha256:research-image"
    assert entry.promotion_status == "SHADOW_READY"
    assert entry.rollback_target == "2.0.0"
    assert entry.created_at == NOW


def test_registry_entry_hyperparameters_are_immutable() -> None:
    entry = _entry()
    with pytest.raises(TypeError):
        entry.hyperparameters["lookback"] = 30


def test_registry_rejects_cross_tenant_readiness() -> None:
    with pytest.raises(ModelRegistryError, match="cross-tenant"):
        ModelRegistryService.build(
            candidate=_candidate(),
            readiness=_readiness(workspace_id="ws-other"),
            model_hash="model-hash",
            hyperparameters={},
            result_hash="result-hash",
        )


def test_registry_rejects_candidate_mismatch() -> None:
    readiness = _readiness()
    wrong = PromotionReadiness(
        readiness_id=readiness.readiness_id,
        workspace_id=readiness.workspace_id,
        user_id=readiness.user_id,
        strategy_id=readiness.strategy_id,
        candidate_version=readiness.candidate_version,
        candidate_id="other-candidate",
        dataset_hash=readiness.dataset_hash,
        code_hash=readiness.code_hash,
        environment_digest=readiness.environment_digest,
        evidence_hashes=readiness.evidence_hashes,
        rollback_version=readiness.rollback_version,
        state=readiness.state,
    )

    with pytest.raises(ModelRegistryError, match="candidate/readiness mismatch"):
        ModelRegistryService.build(
            candidate=_candidate(),
            readiness=wrong,
            model_hash="model-hash",
            hyperparameters={},
            result_hash="result-hash",
        )


def test_registry_rejects_empty_model_hash() -> None:
    with pytest.raises(ModelRegistryError, match="model_hash"):
        ModelRegistryService.build(
            candidate=_candidate(),
            readiness=_readiness(),
            model_hash="",
            hyperparameters={},
            result_hash="result-hash",
        )


def test_registry_entry_round_trips_through_research_artifact() -> None:
    entry = _entry()
    artifact = ModelRegistryService.to_artifact(entry)
    restored = ModelRegistryService.from_artifact(artifact)

    assert artifact.kind is ArtifactKind.MODEL
    assert artifact.artifact_id == "model:trend-v2:2.1.0"
    assert artifact.parent_artifact_id == "model:trend-v2:2.0.0"
    assert artifact.content_hash == "model-hash"
    assert restored == entry


def test_registry_rejects_non_registry_model_artifact() -> None:
    artifact = ResearchArtifact(
        artifact_id="model:other:1",
        workspace_id="ws-1",
        user_id=7,
        kind=ArtifactKind.MODEL,
        version="1",
        content_hash="model-hash",
        parent_artifact_id=None,
        created_at=NOW,
        metadata={"purpose": "unrelated-model-artifact"},
    )
    with pytest.raises(ModelRegistryError, match="unsupported"):
        ModelRegistryService.from_artifact(artifact)


class _MemoryStore:
    def __init__(self) -> None:
        self.artifacts: dict[tuple[str, int, ArtifactKind, str], ResearchArtifact] = {}

    async def append_artifact(self, value: ResearchArtifact) -> None:
        key = (value.workspace_id, value.user_id, value.kind, value.artifact_id)
        existing = self.artifacts.get(key)
        if existing is not None and existing != value:
            raise ValueError("immutable AIEA research record conflict")
        self.artifacts[key] = value

    async def get_artifact(self, *, workspace_id, user_id, kind, artifact_id):
        return self.artifacts.get((workspace_id, user_id, kind, artifact_id))

    async def list_artifacts_for_owner(self, *, workspace_id, user_id, kind=None):
        values = [
            value
            for (ws, uid, artifact_kind, _), value in self.artifacts.items()
            if ws == workspace_id
            and uid == user_id
            and (kind is None or artifact_kind is kind)
        ]
        return tuple(sorted(values, key=lambda item: (item.kind.value, item.artifact_id)))


def test_durable_registry_is_owner_scoped_and_idempotent() -> None:
    async def scenario():
        store = _MemoryStore()
        registry = DurableModelRegistry(store)  # type: ignore[arg-type]
        entry = _entry()
        await registry.register(entry)
        await registry.register(entry)
        found = await registry.get(
            workspace_id="ws-1",
            user_id=7,
            strategy_id="trend-v2",
            version="2.1.0",
        )
        hidden = await registry.get(
            workspace_id="ws-1",
            user_id=8,
            strategy_id="trend-v2",
            version="2.1.0",
        )
        owner = await registry.list_for_owner(workspace_id="ws-1", user_id=7)
        return found, hidden, owner

    found, hidden, owner = asyncio.run(scenario())
    assert found == _entry()
    assert hidden is None
    assert owner == (_entry(),)
