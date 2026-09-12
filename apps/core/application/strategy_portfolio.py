"""Phase 7 strategy catalog, runtime, parity and attribution services."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from apps.core.domain.intents import TradeIntent
from apps.core.domain.strategy_portfolio import (
    LegacyStrategyDisposition,
    LegacyStrategyInventoryEntry,
    StrategyActivationState,
    StrategyAttributionEvent,
    StrategyCatalog,
    StrategyCorrelation,
    StrategyEvaluationContext,
    StrategyFamily,
    StrategyFamilyBenchmark,
    StrategyManifest,
    StrategyPnLAttribution,
    StrategyReturnObservation,
    StrategyRuntimeMode,
    StrategyRuntimeResult,
)
from apps.core.ports.strategy_portfolio import (
    PortfolioAllocationPolicy,
    StrategyPlugin,
)


class StrategyRuntimeError(RuntimeError):
    """Strategy runtime cannot safely produce a canonical result."""


LEGACY_STRATEGY_INVENTORY: tuple[LegacyStrategyInventoryEntry, ...] = (
    LegacyStrategyInventoryEntry(
        "trend_pullback",
        "trend/momentum",
        StrategyFamily.TREND_MOMENTUM,
        LegacyStrategyDisposition.MERGE_CONSOLIDATE,
        "canonical trend/momentum family",
        "EMA pullback is a variant of directional trend following.",
    ),
    LegacyStrategyInventoryEntry(
        "smc",
        "liquidity/market-structure",
        StrategyFamily.LIQUIDITY_MICROSTRUCTURE,
        LegacyStrategyDisposition.REBUILD,
        "canonical liquidity/microstructure family",
        "Umbrella logic mixes sweep/order-block/FVG concepts and needs "
        "causal, costs-aware reconstruction.",
    ),
    LegacyStrategyInventoryEntry(
        "ema_cross",
        "trend/momentum",
        StrategyFamily.TREND_MOMENTUM,
        LegacyStrategyDisposition.MERGE_CONSOLIDATE,
        "canonical trend/momentum family",
        "EMA crossover is not a distinct economic hypothesis.",
    ),
    LegacyStrategyInventoryEntry(
        "scalping",
        "liquidity/market-structure",
        StrategyFamily.LIQUIDITY_MICROSTRUCTURE,
        LegacyStrategyDisposition.RESEARCH_ONLY,
        "microstructure research candidate",
        "Short-horizon candle/volume heuristic is highly cost and latency "
        "sensitive.",
    ),
    LegacyStrategyInventoryEntry(
        "bollinger_squeeze",
        "breakout/volatility",
        StrategyFamily.BREAKOUT_VOLATILITY,
        LegacyStrategyDisposition.MERGE_CONSOLIDATE,
        "canonical breakout/volatility family",
        "Squeeze is a volatility-compression breakout variant.",
    ),
    LegacyStrategyInventoryEntry(
        "mean_reversion",
        "mean-reversion/range",
        StrategyFamily.MEAN_REVERSION_RANGE,
        LegacyStrategyDisposition.KEEP_AS_FAMILY_CANDIDATE,
        "canonical mean-reversion/range family",
        "RSI/Bollinger logic expresses a clear reversion hypothesis.",
    ),
    LegacyStrategyInventoryEntry(
        "trend_following_chop",
        "trend/momentum",
        StrategyFamily.TREND_MOMENTUM,
        LegacyStrategyDisposition.KEEP_AS_FAMILY_CANDIDATE,
        "canonical trend/momentum family",
        "Trend following with regime filter is the strongest legacy "
        "representative of this family.",
    ),
    LegacyStrategyInventoryEntry(
        "statistical_arbitrage",
        "stat-arb/relative-value",
        StrategyFamily.STAT_ARB_RELATIVE_VALUE,
        LegacyStrategyDisposition.KEEP_AS_FAMILY_CANDIDATE,
        "canonical stat-arb/relative-value family",
        "Pair spread z-score expresses a distinct relative-value edge.",
    ),
    LegacyStrategyInventoryEntry(
        "breakout",
        "breakout/volatility",
        StrategyFamily.BREAKOUT_VOLATILITY,
        LegacyStrategyDisposition.KEEP_AS_FAMILY_CANDIDATE,
        "canonical breakout/volatility family",
        "Consolidation breakout with volume confirmation is a clear family "
        "representative.",
    ),
    LegacyStrategyInventoryEntry(
        "range_trading",
        "mean-reversion/range",
        StrategyFamily.MEAN_REVERSION_RANGE,
        LegacyStrategyDisposition.MERGE_CONSOLIDATE,
        "canonical mean-reversion/range family",
        "Range support/resistance bounce overlaps the same reversion edge.",
    ),
    LegacyStrategyInventoryEntry(
        "liquidity_sweep",
        "liquidity/market-structure",
        StrategyFamily.LIQUIDITY_MICROSTRUCTURE,
        LegacyStrategyDisposition.KEEP_AS_FAMILY_CANDIDATE,
        "canonical liquidity/microstructure family",
        "Liquidity sweep/reversal is a distinct market-structure candidate "
        "but still requires execution-aware validation.",
    ),
    LegacyStrategyInventoryEntry(
        "order_block",
        "liquidity/market-structure",
        StrategyFamily.LIQUIDITY_MICROSTRUCTURE,
        LegacyStrategyDisposition.MERGE_CONSOLIDATE,
        "canonical liquidity/microstructure family",
        "Order-block logic overlaps the broader market-structure family.",
    ),
    LegacyStrategyInventoryEntry(
        "fair_value_gap",
        "liquidity/market-structure",
        StrategyFamily.LIQUIDITY_MICROSTRUCTURE,
        LegacyStrategyDisposition.MERGE_CONSOLIDATE,
        "canonical liquidity/microstructure family",
        "FVG logic overlaps the broader market-structure family.",
    ),
    LegacyStrategyInventoryEntry(
        "volume_profile",
        "liquidity/market-structure",
        StrategyFamily.LIQUIDITY_MICROSTRUCTURE,
        LegacyStrategyDisposition.RESEARCH_ONLY,
        "market-structure feature/research candidate",
        "Volume profile is better treated as contextual evidence until a "
        "standalone edge is falsification-tested.",
    ),
    LegacyStrategyInventoryEntry(
        "funding_oi",
        "funding/basis/carry",
        StrategyFamily.FUNDING_BASIS_CARRY,
        LegacyStrategyDisposition.KEEP_AS_FAMILY_CANDIDATE,
        "canonical funding/basis/carry family",
        "Funding and open-interest dynamics express a distinct derivatives "
        "carry/positioning hypothesis.",
    ),
    LegacyStrategyInventoryEntry(
        "volatility_expansion",
        "breakout/volatility",
        StrategyFamily.BREAKOUT_VOLATILITY,
        LegacyStrategyDisposition.MERGE_CONSOLIDATE,
        "canonical breakout/volatility family",
        "Volatility expansion is another breakout-family expression.",
    ),
    LegacyStrategyInventoryEntry(
        "grid_combo",
        "grid-program",
        None,
        LegacyStrategyDisposition.REBUILD,
        "Phase 7G Grid Trading Desk",
        "Grid is a dedicated trading direction and is excluded from normal "
        "StrategyPlugin ownership.",
    ),
)


_COMMON_BENCHMARK_DIMENSIONS = (
    "realistic costs/slippage",
    "OOS and walk-forward stability",
    "parameter and regime stability",
    "cross-symbol robustness",
    "capacity/liquidity",
    "tail risk",
    "incremental portfolio correlation",
    "falsification criteria",
)


STRATEGY_FAMILY_BENCHMARKS: tuple[StrategyFamilyBenchmark, ...] = (
    StrategyFamilyBenchmark(
        StrategyFamily.TREND_MOMENTUM,
        "Persistent directional moves can survive costs when trend strength "
        "and regime filters reduce churn.",
        (
            "https://github.com/QuantConnect/Lean",
            "https://github.com/freqtrade/freqtrade",
            "https://github.com/nautechsystems/nautilus_trader",
        ),
        _COMMON_BENCHMARK_DIMENSIONS,
        StrategyActivationState.RESEARCH_ONLY,
    ),
    StrategyFamilyBenchmark(
        StrategyFamily.MEAN_REVERSION_RANGE,
        "Short-horizon deviations can revert when liquidity and regime "
        "conditions support stable ranges.",
        (
            "https://github.com/QuantConnect/Lean",
            "https://github.com/microsoft/qlib",
            "https://github.com/freqtrade/freqtrade",
        ),
        _COMMON_BENCHMARK_DIMENSIONS,
        StrategyActivationState.RESEARCH_ONLY,
    ),
    StrategyFamilyBenchmark(
        StrategyFamily.BREAKOUT_VOLATILITY,
        "Compression and range breaks can predict volatility expansion when "
        "false-breakout costs are controlled.",
        (
            "https://github.com/freqtrade/freqtrade",
            "https://github.com/QuantConnect/Lean",
            "https://github.com/nautechsystems/nautilus_trader",
        ),
        _COMMON_BENCHMARK_DIMENSIONS,
        StrategyActivationState.RESEARCH_ONLY,
    ),
    StrategyFamilyBenchmark(
        StrategyFamily.LIQUIDITY_MICROSTRUCTURE,
        "Order-flow and liquidity dislocations can produce short-lived edge "
        "only if latency, adverse selection and fees are modeled.",
        (
            "https://github.com/hummingbot/hummingbot",
            "https://github.com/nautechsystems/nautilus_trader",
            "https://github.com/QuantConnect/Lean",
        ),
        _COMMON_BENCHMARK_DIMENSIONS,
        StrategyActivationState.RESEARCH_ONLY,
    ),
    StrategyFamilyBenchmark(
        StrategyFamily.STAT_ARB_RELATIVE_VALUE,
        "Relative mispricing between economically linked instruments can "
        "mean-revert under stable hedge relationships.",
        (
            "https://github.com/microsoft/qlib",
            "https://github.com/QuantConnect/Lean",
            "https://github.com/polakowo/vectorbt",
        ),
        _COMMON_BENCHMARK_DIMENSIONS,
        StrategyActivationState.RESEARCH_ONLY,
    ),
    StrategyFamilyBenchmark(
        StrategyFamily.FUNDING_BASIS_CARRY,
        "Funding/basis dislocations can pay carry or positioning premia when "
        "borrow, transfer and liquidation risks are controlled.",
        (
            "https://github.com/QuantConnect/Lean",
            "https://github.com/freqtrade/freqtrade",
            "https://github.com/nautechsystems/nautilus_trader",
        ),
        _COMMON_BENCHMARK_DIMENSIONS,
        StrategyActivationState.RESEARCH_ONLY,
    ),
    StrategyFamilyBenchmark(
        StrategyFamily.MARKET_MAKING,
        "Spread capture can be profitable only when inventory risk, adverse "
        "selection and venue economics are favorable.",
        (
            "https://github.com/hummingbot/hummingbot",
            "https://github.com/nautechsystems/nautilus_trader",
            "https://github.com/QuantConnect/Lean",
        ),
        _COMMON_BENCHMARK_DIMENSIONS,
        StrategyActivationState.RESEARCH_ONLY,
    ),
)


CANONICAL_FAMILY_SHORTLIST: tuple[StrategyFamily, ...] = tuple(
    item.family for item in STRATEGY_FAMILY_BENCHMARKS
)


RESEARCH_STRATEGY_CATALOG = StrategyCatalog(
    catalog_version="phase7-research-v1",
    entries=tuple(
        StrategyManifest(
            strategy_id=f"family:{family.value.lower()}",
            version="0.1.0-research",
            family=family,
            hypothesis=next(
                item.economic_hypothesis
                for item in STRATEGY_FAMILY_BENCHMARKS
                if item.family is family
            ),
            parameter_schema_version="1",
            data_requirements=("canonical-market-context",),
            risk_requirements=("portfolio-risk-v2",),
            artifact_hash=f"research-family:{family.value}",
            validation_evidence=(),
            activation_state=StrategyActivationState.RESEARCH_ONLY,
            metadata={"production_activation": "not-approved"},
        )
        for family in CANONICAL_FAMILY_SHORTLIST
    ),
)


class StrategyRuntime:
    """Run the same strategy intent semantics in every runtime mode."""

    def __init__(
        self,
        *,
        catalog: StrategyCatalog,
        allocation: PortfolioAllocationPolicy,
    ) -> None:
        self._catalog = catalog
        self._allocation = allocation

    def evaluate(
        self,
        *,
        plugin: StrategyPlugin,
        context: StrategyEvaluationContext,
        mode: StrategyRuntimeMode,
    ) -> StrategyRuntimeResult:
        if not isinstance(mode, StrategyRuntimeMode):
            raise ValueError("mode must be a StrategyRuntimeMode")
        manifest = self._catalog.get(plugin.strategy_id, plugin.version)
        if manifest.activation_state is StrategyActivationState.DISABLED:
            raise StrategyRuntimeError("strategy is disabled")
        intent = plugin.evaluate(context)
        if intent is not None:
            self._validate_lineage(
                manifest=manifest,
                intent=intent,
                context=context,
            )
            intent = self._allocation.allocate(intent, context)
            if intent is not None:
                self._validate_lineage(
                    manifest=manifest,
                    intent=intent,
                    context=context,
                )
        return StrategyRuntimeResult(
            mode=mode,
            manifest=manifest,
            intent=intent,
        )

    @staticmethod
    def _validate_lineage(
        *,
        manifest: StrategyManifest,
        intent: TradeIntent,
        context: StrategyEvaluationContext,
    ) -> None:
        if intent.user_id != context.user_id:
            raise StrategyRuntimeError("strategy intent user mismatch")
        if intent.strategy != manifest.strategy_id:
            raise StrategyRuntimeError("strategy intent ID mismatch")
        if intent.strategy_version != manifest.version:
            raise StrategyRuntimeError("strategy intent version mismatch")


class StrategySemanticParity:
    """Compare canonical intent semantics across runtime modes."""

    def __init__(self, runtime: StrategyRuntime) -> None:
        self._runtime = runtime

    def assert_equivalent(
        self,
        *,
        plugin: StrategyPlugin,
        context: StrategyEvaluationContext,
        left_mode: StrategyRuntimeMode,
        right_mode: StrategyRuntimeMode,
    ) -> tuple[StrategyRuntimeResult, StrategyRuntimeResult]:
        left = self._runtime.evaluate(
            plugin=plugin,
            context=context,
            mode=left_mode,
        )
        right = self._runtime.evaluate(
            plugin=plugin,
            context=context,
            mode=right_mode,
        )
        if self._intent_signature(left.intent) != self._intent_signature(
            right.intent
        ):
            raise StrategyRuntimeError("strategy semantic parity mismatch")
        return left, right

    @staticmethod
    def _intent_signature(intent: TradeIntent | None) -> object:
        if intent is None:
            return None
        return (
            intent.user_id,
            intent.strategy,
            intent.strategy_version,
            intent.source,
            intent.kind,
            intent.shape,
            tuple(
                (
                    leg.leg_id,
                    leg.instrument_id,
                    leg.account_id,
                    leg.side,
                    leg.quantity,
                )
                for leg in intent.legs
            ),
            tuple(sorted(intent.metadata.items())),
        )


class StrategyAttributionAnalytics:
    """Deterministic per-strategy PnL and return-correlation analytics."""

    @staticmethod
    def pnl(
        events: tuple[StrategyAttributionEvent, ...],
    ) -> tuple[StrategyPnLAttribution, ...]:
        if not isinstance(events, tuple):
            raise ValueError("events must be a tuple")
        event_ids = tuple(item.event_id for item in events)
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("duplicate attribution event_id")
        grouped: dict[
            tuple[str, str],
            list[StrategyAttributionEvent],
        ] = defaultdict(list)
        for event in events:
            if not isinstance(event, StrategyAttributionEvent):
                raise ValueError(
                    "events must contain StrategyAttributionEvent values"
                )
            grouped[(event.strategy_id, event.strategy_version)].append(event)
        result: list[StrategyPnLAttribution] = []
        for key in sorted(grouped):
            items = grouped[key]
            realized = sum((item.realized_pnl for item in items), Decimal("0"))
            fees = sum((item.fees for item in items), Decimal("0"))
            funding = sum((item.funding for item in items), Decimal("0"))
            result.append(
                StrategyPnLAttribution(
                    strategy_id=key[0],
                    strategy_version=key[1],
                    realized_pnl=realized,
                    fees=fees,
                    funding=funding,
                    net_pnl=realized - fees + funding,
                    event_count=len(items),
                )
            )
        return tuple(result)

    @staticmethod
    def correlations(
        observations: tuple[StrategyReturnObservation, ...],
    ) -> tuple[StrategyCorrelation, ...]:
        if not isinstance(observations, tuple):
            raise ValueError("observations must be a tuple")
        series: dict[
            tuple[str, str],
            dict[datetime, Decimal],
        ] = defaultdict(dict)
        for item in observations:
            if not isinstance(item, StrategyReturnObservation):
                raise ValueError(
                    "observations must contain "
                    "StrategyReturnObservation values"
                )
            key = (item.strategy_id, item.strategy_version)
            if item.period_at in series[key]:
                raise ValueError("duplicate strategy return period")
            series[key][item.period_at] = item.return_ratio
        keys = sorted(series)
        results: list[StrategyCorrelation] = []
        for left_index, left_key in enumerate(keys):
            for right_key in keys[left_index + 1:]:
                common = sorted(set(series[left_key]) & set(series[right_key]))
                if len(common) < 2:
                    continue
                left_values = [series[left_key][period] for period in common]
                right_values = [series[right_key][period] for period in common]
                correlation = _pearson(left_values, right_values)
                results.append(
                    StrategyCorrelation(
                        left_strategy_id=left_key[0],
                        left_strategy_version=left_key[1],
                        right_strategy_id=right_key[0],
                        right_strategy_version=right_key[1],
                        correlation=correlation,
                        overlapping_periods=len(common),
                    )
                )
        return tuple(results)


def _pearson(left: list[Decimal], right: list[Decimal]) -> Decimal:
    count = Decimal(len(left))
    left_mean = sum(left, Decimal("0")) / count
    right_mean = sum(right, Decimal("0")) / count
    covariance = sum(
        (
            (left_value - left_mean) * (right_value - right_mean)
            for left_value, right_value in zip(left, right, strict=True)
        ),
        Decimal("0"),
    )
    left_variance = sum(
        ((value - left_mean) ** 2 for value in left),
        Decimal("0"),
    )
    right_variance = sum(
        ((value - right_mean) ** 2 for value in right),
        Decimal("0"),
    )
    denominator = (left_variance * right_variance).sqrt()
    if denominator == 0:
        return Decimal("0")
    return covariance / denominator
