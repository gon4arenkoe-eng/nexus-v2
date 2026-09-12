"""Canonical strategy portfolio contracts for NEXUS V2 Phase 7."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from apps.core.domain.intents import TradeIntent
from packages.contracts.primitives import (
    normalize_utc_datetime,
    require_non_negative_decimal,
)


class StrategyFamily(StrEnum):
    TREND_MOMENTUM = "TREND_MOMENTUM"
    MEAN_REVERSION_RANGE = "MEAN_REVERSION_RANGE"
    BREAKOUT_VOLATILITY = "BREAKOUT_VOLATILITY"
    LIQUIDITY_MICROSTRUCTURE = "LIQUIDITY_MICROSTRUCTURE"
    STAT_ARB_RELATIVE_VALUE = "STAT_ARB_RELATIVE_VALUE"
    FUNDING_BASIS_CARRY = "FUNDING_BASIS_CARRY"
    MARKET_MAKING = "MARKET_MAKING"


class LegacyStrategyDisposition(StrEnum):
    KEEP_AS_FAMILY_CANDIDATE = "KEEP_AS_FAMILY_CANDIDATE"
    MERGE_CONSOLIDATE = "MERGE_CONSOLIDATE"
    REBUILD = "REBUILD"
    RESEARCH_ONLY = "RESEARCH_ONLY"
    DEPRECATE = "DEPRECATE"


class StrategyActivationState(StrEnum):
    DISABLED = "DISABLED"
    RESEARCH_ONLY = "RESEARCH_ONLY"
    SHADOW_ONLY = "SHADOW_ONLY"


class StrategyRuntimeMode(StrEnum):
    BACKTEST = "BACKTEST"
    PAPER = "PAPER"
    SHADOW = "SHADOW"
    LIVE_SEMANTICS = "LIVE_SEMANTICS"


class StrategyScorecardDecision(StrEnum):
    REJECT = "REJECT"
    RESEARCH_ONLY = "RESEARCH_ONLY"
    FAMILY_CANDIDATE = "FAMILY_CANDIDATE"


def _require_text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _require_unit_interval(value: Decimal, *, field_name: str) -> Decimal:
    normalized = require_non_negative_decimal(value, field_name=field_name)
    if normalized > Decimal("1"):
        raise ValueError(f"{field_name} must be <= 1")
    return normalized


@dataclass(frozen=True, slots=True)
class LegacyStrategyInventoryEntry:
    legacy_name: str
    cluster: str
    family: StrategyFamily | None
    disposition: LegacyStrategyDisposition
    target: str
    rationale: str

    def __post_init__(self) -> None:
        for field_name in (
            "legacy_name",
            "cluster",
            "target",
            "rationale",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )
        if self.family is not None and not isinstance(
            self.family,
            StrategyFamily,
        ):
            raise ValueError("family must be a StrategyFamily or None")
        if not isinstance(self.disposition, LegacyStrategyDisposition):
            raise ValueError(
                "disposition must be a LegacyStrategyDisposition"
            )


@dataclass(frozen=True, slots=True)
class StrategyFamilyBenchmark:
    family: StrategyFamily
    economic_hypothesis: str
    references: tuple[str, ...]
    benchmark_dimensions: tuple[str, ...]
    production_status: StrategyActivationState

    def __post_init__(self) -> None:
        if not isinstance(self.family, StrategyFamily):
            raise ValueError("family must be a StrategyFamily")
        object.__setattr__(
            self,
            "economic_hypothesis",
            _require_text(
                self.economic_hypothesis,
                field_name="economic_hypothesis",
            ),
        )
        for field_name in ("references", "benchmark_dimensions"):
            values = getattr(self, field_name)
            if not isinstance(values, tuple) or not values:
                raise ValueError(f"{field_name} must be a non-empty tuple")
            if not all(
                isinstance(item, str) and item.strip()
                for item in values
            ):
                raise ValueError(
                    f"{field_name} must contain non-empty strings"
                )
        if not isinstance(self.production_status, StrategyActivationState):
            raise ValueError(
                "production_status must be a StrategyActivationState"
            )


@dataclass(frozen=True, slots=True)
class StrategyManifest:
    strategy_id: str
    version: str
    family: StrategyFamily
    hypothesis: str
    parameter_schema_version: str
    data_requirements: tuple[str, ...]
    risk_requirements: tuple[str, ...]
    artifact_hash: str
    validation_evidence: tuple[str, ...]
    activation_state: StrategyActivationState
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for field_name in (
            "strategy_id",
            "version",
            "hypothesis",
            "parameter_schema_version",
            "artifact_hash",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )
        if not isinstance(self.family, StrategyFamily):
            raise ValueError("family must be a StrategyFamily")
        for field_name in (
            "data_requirements",
            "risk_requirements",
            "validation_evidence",
        ):
            values = getattr(self, field_name)
            if not isinstance(values, tuple):
                raise ValueError(f"{field_name} must be a tuple")
            if not all(
                isinstance(item, str) and item.strip()
                for item in values
            ):
                raise ValueError(
                    f"{field_name} must contain non-empty strings"
                )
        if not isinstance(self.activation_state, StrategyActivationState):
            raise ValueError(
                "activation_state must be a StrategyActivationState"
            )
        if (
            self.activation_state is StrategyActivationState.SHADOW_ONLY
            and not self.validation_evidence
        ):
            raise ValueError("shadow strategy requires validation evidence")
        if not isinstance(self.metadata, Mapping):
            raise ValueError("metadata must be a mapping")
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )

    @property
    def key(self) -> tuple[str, str]:
        return (self.strategy_id, self.version)


@dataclass(frozen=True, slots=True)
class StrategyCatalog:
    catalog_version: str
    entries: tuple[StrategyManifest, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "catalog_version",
            _require_text(
                self.catalog_version,
                field_name="catalog_version",
            ),
        )
        if not isinstance(self.entries, tuple):
            raise ValueError("entries must be a tuple")
        if not all(
            isinstance(item, StrategyManifest)
            for item in self.entries
        ):
            raise ValueError(
                "entries must contain StrategyManifest values"
            )
        ordered = tuple(sorted(self.entries, key=lambda item: item.key))
        keys = tuple(item.key for item in ordered)
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate strategy/version in catalog")
        object.__setattr__(self, "entries", ordered)

    def get(self, strategy_id: str, version: str) -> StrategyManifest:
        key = (
            _require_text(strategy_id, field_name="strategy_id"),
            _require_text(version, field_name="version"),
        )
        for entry in self.entries:
            if entry.key == key:
                return entry
        raise KeyError(f"strategy not found: {key[0]}@{key[1]}")


@dataclass(frozen=True, slots=True)
class StrategyResearchScorecard:
    oos_expectancy: Decimal
    profit_factor_score: Decimal
    drawdown_resilience: Decimal
    walk_forward_stability: Decimal
    parameter_stability: Decimal
    cross_symbol_stability: Decimal
    regime_stability: Decimal
    capacity_score: Decimal
    cost_robustness: Decimal
    tail_risk_resilience: Decimal
    incremental_diversification: Decimal
    falsification_passed: bool

    def __post_init__(self) -> None:
        for field_name in (
            "oos_expectancy",
            "profit_factor_score",
            "drawdown_resilience",
            "walk_forward_stability",
            "parameter_stability",
            "cross_symbol_stability",
            "regime_stability",
            "capacity_score",
            "cost_robustness",
            "tail_risk_resilience",
            "incremental_diversification",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_interval(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )
        if not isinstance(self.falsification_passed, bool):
            raise ValueError("falsification_passed must be bool")

    @property
    def weighted_score(self) -> Decimal:
        values = (
            self.oos_expectancy,
            self.profit_factor_score,
            self.drawdown_resilience,
            self.walk_forward_stability,
            self.parameter_stability,
            self.cross_symbol_stability,
            self.regime_stability,
            self.capacity_score,
            self.cost_robustness,
            self.tail_risk_resilience,
            self.incremental_diversification,
        )
        return sum(values, Decimal("0")) / Decimal(len(values))

    @property
    def decision(self) -> StrategyScorecardDecision:
        if not self.falsification_passed:
            return StrategyScorecardDecision.REJECT
        if self.weighted_score >= Decimal("0.70"):
            return StrategyScorecardDecision.FAMILY_CANDIDATE
        return StrategyScorecardDecision.RESEARCH_ONLY


@dataclass(frozen=True, slots=True)
class StrategyEvaluationContext:
    user_id: int
    observed_at: datetime
    features: Mapping[str, Decimal]

    def __post_init__(self) -> None:
        if isinstance(self.user_id, bool) or not isinstance(self.user_id, int):
            raise ValueError("user_id must be an integer")
        if self.user_id <= 0:
            raise ValueError("user_id must be positive")
        object.__setattr__(
            self,
            "observed_at",
            normalize_utc_datetime(self.observed_at, field_name="observed_at"),
        )
        if not isinstance(self.features, Mapping):
            raise ValueError("features must be a mapping")
        normalized: dict[str, Decimal] = {}
        for name, value in self.features.items():
            key = _require_text(name, field_name="feature name")
            if not isinstance(value, Decimal) or not value.is_finite():
                raise ValueError("feature values must be finite Decimal")
            normalized[key] = value
        object.__setattr__(
            self,
            "features",
            MappingProxyType(normalized),
        )


@dataclass(frozen=True, slots=True)
class StrategyRuntimeResult:
    mode: StrategyRuntimeMode
    manifest: StrategyManifest
    intent: TradeIntent | None

    def __post_init__(self) -> None:
        if not isinstance(self.mode, StrategyRuntimeMode):
            raise ValueError("mode must be a StrategyRuntimeMode")
        if not isinstance(self.manifest, StrategyManifest):
            raise ValueError("manifest must be a StrategyManifest")
        if (
            self.intent is not None
            and not isinstance(self.intent, TradeIntent)
        ):
            raise ValueError("intent must be TradeIntent or None")


@dataclass(frozen=True, slots=True)
class StrategyAttributionEvent:
    event_id: str
    strategy_id: str
    strategy_version: str
    occurred_at: datetime
    realized_pnl: Decimal
    fees: Decimal = Decimal("0")
    funding: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        for field_name in ("event_id", "strategy_id", "strategy_version"):
            object.__setattr__(
                self,
                field_name,
                _require_text(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )
        object.__setattr__(
            self,
            "occurred_at",
            normalize_utc_datetime(self.occurred_at, field_name="occurred_at"),
        )
        for field_name in ("realized_pnl", "fees", "funding"):
            value = getattr(self, field_name)
            if not isinstance(value, Decimal) or not value.is_finite():
                raise ValueError(f"{field_name} must be finite Decimal")

    @property
    def net_pnl(self) -> Decimal:
        return self.realized_pnl - self.fees + self.funding


@dataclass(frozen=True, slots=True)
class StrategyPnLAttribution:
    strategy_id: str
    strategy_version: str
    realized_pnl: Decimal
    fees: Decimal
    funding: Decimal
    net_pnl: Decimal
    event_count: int


@dataclass(frozen=True, slots=True)
class StrategyReturnObservation:
    strategy_id: str
    strategy_version: str
    period_at: datetime
    return_ratio: Decimal

    def __post_init__(self) -> None:
        for field_name in ("strategy_id", "strategy_version"):
            object.__setattr__(
                self,
                field_name,
                _require_text(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )
        object.__setattr__(
            self,
            "period_at",
            normalize_utc_datetime(self.period_at, field_name="period_at"),
        )
        if (
            not isinstance(self.return_ratio, Decimal)
            or not self.return_ratio.is_finite()
        ):
            raise ValueError("return_ratio must be finite Decimal")


@dataclass(frozen=True, slots=True)
class StrategyCorrelation:
    left_strategy_id: str
    left_strategy_version: str
    right_strategy_id: str
    right_strategy_version: str
    correlation: Decimal
    overlapping_periods: int
