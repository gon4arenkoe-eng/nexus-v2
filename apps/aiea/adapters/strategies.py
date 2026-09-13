"""Deterministic strategy signal functions for AIEA backtesting.

Each function receives only the closes observed *up to and including* the
current bar and returns a position in {-1, 0, 1} for the *next* bar. Because
each function only ever looks at `closes[:i+1]` when deciding the position
to hold going into bar `i+1`, using it inside `backtest_worker.simulate`
cannot leak future information into a decision -- this is what lets the
LOOKAHEAD_LEAKAGE falsification check be a genuine structural guarantee
rather than a self-reported flag.

These are intentionally simple, explainable archetypes (not tuned for
performance) -- they exist to give the falsification pipeline something
real to accept or reject, and to correspond 1:1 with the hypothesis
statements produced by `hypothesis_factory.py`.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Callable, Sequence

StrategySignal = Callable[[Sequence[Decimal]], int]


def _sma(values: Sequence[Decimal], window: int) -> Decimal | None:
    if len(values) < window:
        return None
    tail = values[-window:]
    return sum(tail) / Decimal(window)


def trend_continuation(closes: Sequence[Decimal], *, window: int = 24) -> int:
    """Long if price is above its rolling mean, short if below."""
    sma = _sma(closes, window)
    if sma is None:
        return 0
    latest = closes[-1]
    if latest > sma * Decimal("1.001"):
        return 1
    if latest < sma * Decimal("0.999"):
        return -1
    return 0


def mean_reversion(closes: Sequence[Decimal], *, window: int = 24) -> int:
    """Fade moves that sit far from the rolling mean (z-score style)."""
    sma = _sma(closes, window)
    if sma is None or len(closes) < window:
        return 0
    tail = closes[-window:]
    mean = sma
    variance = sum((c - mean) ** 2 for c in tail) / Decimal(window)
    std = variance.sqrt() if variance > 0 else Decimal("0")
    if std == 0:
        return 0
    z = (closes[-1] - mean) / std
    if z > Decimal("1.2"):
        return -1
    if z < Decimal("-1.2"):
        return 1
    return 0


def volatility_expansion(closes: Sequence[Decimal], *, window: int = 24) -> int:
    """Breakout: go with the direction of a new N-bar high/low."""
    if len(closes) <= window:
        return 0
    prior = closes[-window - 1:-1]
    latest = closes[-1]
    if latest > max(prior):
        return 1
    if latest < min(prior):
        return -1
    return 0


def perturbed(
    base: StrategySignal,
    *,
    window_override: int,
) -> StrategySignal:
    """Wrap a strategy with a different lookback window.

    Used by the PARAMETER_STABILITY falsification check to verify a
    candidate's behaviour does not flip sign under a small, reasonable
    perturbation of its own parameters.
    """

    def _wrapped(closes: Sequence[Decimal]) -> int:
        return base(closes, window=window_override)  # type: ignore[call-arg]

    return _wrapped


STRATEGY_REGISTRY: dict[str, StrategySignal] = {
    "trend-continuation": trend_continuation,
    "mean-reversion": mean_reversion,
    "volatility-expansion": volatility_expansion,
}


def resolve_strategy(strategy_id: str) -> StrategySignal:
    try:
        return STRATEGY_REGISTRY[strategy_id]
    except KeyError as exc:
        known = ", ".join(sorted(STRATEGY_REGISTRY))
        raise ValueError(
            f"unknown strategy_id {strategy_id!r}; known strategies: {known}"
        ) from exc
