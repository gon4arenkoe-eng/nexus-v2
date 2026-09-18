"""Deterministic AIEA drift/freshness monitoring and champion/challenger adaptation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
import json

from apps.aiea.domain.research import ArtifactKind, DriftState, ResearchArtifact
from apps.aiea.ports.research import ResearchRecordStore


DRIFT_SCHEMA_VERSION = "nexus.aiea.drift-monitor.v1"


class AdaptationAction(StrEnum):
    NONE = "NONE"
    WATCH = "WATCH"
    RESEARCH_CHALLENGER = "RESEARCH_CHALLENGER"
    COMPARE_CHALLENGER = "COMPARE_CHALLENGER"
    PROMOTION_REVIEW = "PROMOTION_REVIEW"


class ComparisonState(StrEnum):
    NOT_AVAILABLE = "NOT_AVAILABLE"
    CHAMPION_RETAINS = "CHAMPION_RETAINS"
    CHALLENGER_RESEARCH_WORTHY = "CHALLENGER_RESEARCH_WORTHY"
    CHALLENGER_PROMOTION_REVIEW = "CHALLENGER_PROMOTION_REVIEW"


@dataclass(frozen=True, slots=True)
class DriftPolicy:
    max_evidence_age: timedelta = timedelta(days=7)
    watch_performance_ratio: Decimal = Decimal("0.75")
    degraded_performance_ratio: Decimal = Decimal("0.55")
    challenger_research_lift: Decimal = Decimal("0.03")
    challenger_promotion_lift: Decimal = Decimal("0.08")

    def __post_init__(self) -> None:
        if self.max_evidence_age <= timedelta(0):
            raise ValueError("max_evidence_age must be positive")
        if not (
            Decimal("0") < self.degraded_performance_ratio
            < self.watch_performance_ratio <= Decimal("1")
        ):
            raise ValueError("performance thresholds are invalid")
        if not (
            Decimal("0") <= self.challenger_research_lift
            <= self.challenger_promotion_lift
        ):
            raise ValueError("challenger lift thresholds are invalid")


@dataclass(frozen=True, slots=True)
class DriftObservation:
    workspace_id: str
    user_id: int
    strategy_id: str
    champion_version: str
    observed_at: datetime
    evidence_at: datetime
    baseline_score: Decimal
    current_score: Decimal
    evidence_hash: str
    challenger_version: str | None = None
    challenger_score: Decimal | None = None
    challenger_evidence_hash: str | None = None

    def __post_init__(self) -> None:
        for name in ("workspace_id", "strategy_id", "champion_version", "evidence_hash"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        if self.user_id <= 0:
            raise ValueError("user_id must be positive")
        for name in ("observed_at", "evidence_at"):
            value = getattr(self, name)
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
        if self.evidence_at > self.observed_at:
            raise ValueError("evidence_at cannot be in the future")
        if self.baseline_score <= Decimal("0"):
            raise ValueError("baseline_score must be positive")
        if self.current_score < Decimal("0"):
            raise ValueError("current_score cannot be negative")
        if self.challenger_version is None:
            if self.challenger_score is not None or self.challenger_evidence_hash is not None:
                raise ValueError("challenger evidence requires challenger_version")
        else:
            if not self.challenger_version.strip() or self.challenger_version == self.champion_version:
                raise ValueError("challenger_version must differ from champion_version")
            if self.challenger_score is None or self.challenger_score < Decimal("0"):
                raise ValueError("challenger_score is required and non-negative")
            if not self.challenger_evidence_hash:
                raise ValueError("challenger_evidence_hash is required")


@dataclass(frozen=True, slots=True)
class ChampionChallengerDecision:
    decision_id: str
    workspace_id: str
    user_id: int
    strategy_id: str
    champion_version: str
    challenger_version: str | None
    state: DriftState
    action: AdaptationAction
    comparison: ComparisonState
    observed_at: datetime
    evidence_age_seconds: int
    performance_ratio: Decimal
    freshness_ratio: Decimal
    challenger_lift: Decimal | None
    evidence_hashes: tuple[str, ...]
    decision_hash: str

    @property
    def live_mutation_allowed(self) -> bool:
        return False


class DriftMonitorService:
    """Compute deterministic drift evidence; never activate or mutate live versions."""

    def __init__(self, policy: DriftPolicy | None = None) -> None:
        self._policy = policy or DriftPolicy()

    def assess(self, observation: DriftObservation) -> ChampionChallengerDecision:
        age = observation.observed_at - observation.evidence_at
        age_seconds = max(0, int(age.total_seconds()))
        max_seconds = int(self._policy.max_evidence_age.total_seconds())
        freshness = max(Decimal("0"), Decimal("1") - (Decimal(age_seconds) / Decimal(max_seconds)))
        performance = observation.current_score / observation.baseline_score
        if performance > Decimal("1"):
            performance = Decimal("1")

        if age > self._policy.max_evidence_age:
            state = DriftState.UNKNOWN
            action = AdaptationAction.RESEARCH_CHALLENGER
        elif performance < self._policy.degraded_performance_ratio:
            state = DriftState.DEGRADED
            action = AdaptationAction.RESEARCH_CHALLENGER
        elif performance < self._policy.watch_performance_ratio:
            state = DriftState.WATCH
            action = AdaptationAction.WATCH
        else:
            state = DriftState.HEALTHY
            action = AdaptationAction.NONE

        comparison = ComparisonState.NOT_AVAILABLE
        lift: Decimal | None = None
        evidence_hashes = [observation.evidence_hash]
        if observation.challenger_version is not None:
            assert observation.challenger_score is not None
            assert observation.challenger_evidence_hash is not None
            evidence_hashes.append(observation.challenger_evidence_hash)
            if observation.current_score == Decimal("0"):
                lift = Decimal("1") if observation.challenger_score > Decimal("0") else Decimal("0")
            else:
                lift = (observation.challenger_score / observation.current_score) - Decimal("1")
            if lift >= self._policy.challenger_promotion_lift:
                comparison = ComparisonState.CHALLENGER_PROMOTION_REVIEW
                action = AdaptationAction.PROMOTION_REVIEW
            elif lift >= self._policy.challenger_research_lift:
                comparison = ComparisonState.CHALLENGER_RESEARCH_WORTHY
                action = AdaptationAction.COMPARE_CHALLENGER
            else:
                comparison = ComparisonState.CHAMPION_RETAINS
                if state is DriftState.HEALTHY:
                    action = AdaptationAction.NONE

        payload = {
            "workspace_id": observation.workspace_id,
            "user_id": observation.user_id,
            "strategy_id": observation.strategy_id,
            "champion_version": observation.champion_version,
            "challenger_version": observation.challenger_version,
            "state": state.value,
            "action": action.value,
            "comparison": comparison.value,
            "observed_at": observation.observed_at.isoformat(),
            "evidence_age_seconds": age_seconds,
            "performance_ratio": str(performance),
            "freshness_ratio": str(freshness),
            "challenger_lift": None if lift is None else str(lift),
            "evidence_hashes": evidence_hashes,
        }
        digest = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return ChampionChallengerDecision(
            decision_id=f"drift:{observation.strategy_id}:{digest[:24]}",
            workspace_id=observation.workspace_id,
            user_id=observation.user_id,
            strategy_id=observation.strategy_id,
            champion_version=observation.champion_version,
            challenger_version=observation.challenger_version,
            state=state,
            action=action,
            comparison=comparison,
            observed_at=observation.observed_at,
            evidence_age_seconds=age_seconds,
            performance_ratio=performance,
            freshness_ratio=freshness,
            challenger_lift=lift,
            evidence_hashes=tuple(evidence_hashes),
            decision_hash=digest,
        )


class DurableDriftEvidence:
    """Persist drift decisions in the existing immutable tenant-scoped research journal."""

    def __init__(self, store: ResearchRecordStore) -> None:
        self._store = store

    async def append(self, decision: ChampionChallengerDecision) -> None:
        await self._store.append_artifact(self.to_artifact(decision))

    async def list_for_owner(self, *, workspace_id: str, user_id: int) -> tuple[ChampionChallengerDecision, ...]:
        artifacts = await self._store.list_artifacts_for_owner(
            workspace_id=workspace_id,
            user_id=user_id,
            kind=ArtifactKind.EVIDENCE,
        )
        values = tuple(
            self.from_artifact(item)
            for item in artifacts
            if item.metadata.get("schema_version") == DRIFT_SCHEMA_VERSION
        )
        return tuple(sorted(values, key=lambda item: (item.observed_at, item.decision_id)))

    @staticmethod
    def to_artifact(decision: ChampionChallengerDecision) -> ResearchArtifact:
        metadata = {
            "schema_version": DRIFT_SCHEMA_VERSION,
            "strategy_id": decision.strategy_id,
            "champion_version": decision.champion_version,
            "challenger_version": decision.challenger_version,
            "state": decision.state.value,
            "action": decision.action.value,
            "comparison": decision.comparison.value,
            "observed_at": decision.observed_at.isoformat(),
            "evidence_age_seconds": decision.evidence_age_seconds,
            "performance_ratio": str(decision.performance_ratio),
            "freshness_ratio": str(decision.freshness_ratio),
            "challenger_lift": None if decision.challenger_lift is None else str(decision.challenger_lift),
            "evidence_hashes": list(decision.evidence_hashes),
            "live_mutation_allowed": False,
        }
        return ResearchArtifact(
            artifact_id=decision.decision_id,
            workspace_id=decision.workspace_id,
            user_id=decision.user_id,
            kind=ArtifactKind.EVIDENCE,
            version=DRIFT_SCHEMA_VERSION,
            content_hash=decision.decision_hash,
            parent_artifact_id=None,
            created_at=decision.observed_at,
            metadata=metadata,
        )

    @staticmethod
    def from_artifact(artifact: ResearchArtifact) -> ChampionChallengerDecision:
        if artifact.kind is not ArtifactKind.EVIDENCE or artifact.metadata.get("schema_version") != DRIFT_SCHEMA_VERSION:
            raise ValueError("artifact is not AIEA drift evidence")
        m = artifact.metadata
        evidence_hashes = m.get("evidence_hashes")
        if not isinstance(evidence_hashes, list) or not evidence_hashes:
            raise ValueError("drift artifact evidence_hashes are invalid")
        challenger_version = m.get("challenger_version")
        challenger_lift = m.get("challenger_lift")
        return ChampionChallengerDecision(
            decision_id=artifact.artifact_id,
            workspace_id=artifact.workspace_id,
            user_id=artifact.user_id,
            strategy_id=str(m["strategy_id"]),
            champion_version=str(m["champion_version"]),
            challenger_version=None if challenger_version is None else str(challenger_version),
            state=DriftState(str(m["state"])),
            action=AdaptationAction(str(m["action"])),
            comparison=ComparisonState(str(m["comparison"])),
            observed_at=datetime.fromisoformat(str(m["observed_at"])),
            evidence_age_seconds=(
                m["evidence_age_seconds"]
                if isinstance(m["evidence_age_seconds"], int)
                else int(str(m["evidence_age_seconds"]))
            ),
            performance_ratio=Decimal(str(m["performance_ratio"])),
            freshness_ratio=Decimal(str(m["freshness_ratio"])),
            challenger_lift=None if challenger_lift is None else Decimal(str(challenger_lift)),
            evidence_hashes=tuple(str(value) for value in evidence_hashes),
            decision_hash=artifact.content_hash,
        )
