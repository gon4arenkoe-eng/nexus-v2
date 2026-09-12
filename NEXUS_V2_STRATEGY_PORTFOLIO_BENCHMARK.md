# NEXUS V2 Phase 7 — Strategy Portfolio Benchmark

Status: implementation evidence for `NEXUS_V2_STRATEGY_PORTFOLIO_OK`.

## Scope and safety

Phase 7 creates a canonical strategy catalog/runtime and portfolio analytics. It does **not** certify any strategy for production live trading. Every canonical family begins in `RESEARCH_ONLY`; activation still requires later research/promotion evidence and all risk/execution gates. Strategies create canonical `TradeIntent` only. They do not submit venue orders.

Grid is explicitly excluded from the normal Strategy Portfolio and is transferred to Phase 7G.

## Legacy inventory and clustering

| Legacy strategy | Cluster / canonical family | Migration classification | Phase 7 decision |
|---|---|---|---|
| `trend_pullback` | Trend / Momentum | MERGE/CONSOLIDATE | Merge into canonical trend family |
| `smc` | Liquidity / Microstructure | REBUILD | Rebuild causally with costs and execution assumptions |
| `ema_cross` | Trend / Momentum | MERGE/CONSOLIDATE | Merge; indicator variation is not a distinct economic edge |
| `scalping` | Liquidity / Microstructure | RESEARCH ONLY | Latency/cost-sensitive; no production eligibility assumed |
| `bollinger_squeeze` | Breakout / Volatility | MERGE/CONSOLIDATE | Merge into volatility-expansion family |
| `mean_reversion` | Mean Reversion / Range | KEEP AS FAMILY CANDIDATE | Canonical family representative candidate |
| `trend_following_chop` | Trend / Momentum | KEEP AS FAMILY CANDIDATE | Canonical family representative candidate |
| `statistical_arbitrage` | Stat-Arb / Relative Value | KEEP AS FAMILY CANDIDATE | Distinct relative-value hypothesis |
| `breakout` | Breakout / Volatility | KEEP AS FAMILY CANDIDATE | Canonical family representative candidate |
| `range_trading` | Mean Reversion / Range | MERGE/CONSOLIDATE | Merge into reversion/range family |
| `liquidity_sweep` | Liquidity / Microstructure | KEEP AS FAMILY CANDIDATE | Candidate, but execution-aware validation required |
| `order_block` | Liquidity / Microstructure | MERGE/CONSOLIDATE | Merge into broader market-structure family |
| `fair_value_gap` | Liquidity / Microstructure | MERGE/CONSOLIDATE | Merge into broader market-structure family |
| `volume_profile` | Liquidity / Microstructure | RESEARCH ONLY | Treat as contextual feature until standalone edge is falsified/tested |
| `funding_oi` | Funding / Basis / Carry | KEEP AS FAMILY CANDIDATE | Distinct derivatives/carry hypothesis |
| `volatility_expansion` | Breakout / Volatility | MERGE/CONSOLIDATE | Merge into breakout/volatility family |
| `grid_combo` | Grid Program | REBUILD | Move to Phase 7G Grid Trading Desk |

## Canonical family shortlist

1. Trend / Momentum
2. Mean Reversion / Range
3. Breakout / Volatility Expansion
4. Liquidity / Microstructure
5. Statistical Arbitrage / Relative Value
6. Funding / Basis / Carry
7. Market Making

Market Making is intentionally retained as a research family even though the legacy registry has no canonical standalone market-making strategy. It must be justified by venue economics before promotion.

## GitHub/reference benchmark

Phase 7 uses references for architecture/methodology comparison, not blind code reuse.

| Family | Primary references | Benchmark emphasis |
|---|---|---|
| Trend / Momentum | QuantConnect LEAN, Freqtrade, NautilusTrader | event semantics, costs, OOS/WF stability, churn |
| Mean Reversion / Range | Qlib, LEAN, Freqtrade | risk-adjusted return, regime stability, capacity |
| Breakout / Volatility | Freqtrade, LEAN, NautilusTrader | false-breakout costs, stop/exit parity, slippage |
| Liquidity / Microstructure | Hummingbot, NautilusTrader, LEAN | latency, adverse selection, inventory/execution realism |
| Stat-Arb / Relative Value | Qlib, LEAN, VectorBT | hedge stability, correlation drift, costs/capacity |
| Funding / Basis / Carry | LEAN, Freqtrade, NautilusTrader | historical funding integrity, borrow/transfer/liquidation costs |
| Market Making | Hummingbot, NautilusTrader, LEAN | inventory control, spread capture, adverse selection, venue economics |

References:

- https://github.com/nautechsystems/nautilus_trader
- https://github.com/hummingbot/hummingbot
- https://github.com/QuantConnect/Lean
- https://github.com/freqtrade/freqtrade
- https://github.com/microsoft/qlib
- https://github.com/polakowo/vectorbt

## Required research dimensions before strategy promotion

Every strategy candidate remains subject to later evidence for:

- realistic fees, slippage and funding/borrow costs;
- OOS and walk-forward performance;
- parameter stability;
- regime stability;
- cross-symbol/cross-market robustness;
- capacity/liquidity;
- tail risk;
- latency sensitivity where relevant;
- incremental correlation/diversification contribution;
- explicit falsification criteria.

A high backtest score alone cannot promote a strategy.

## Runtime/parity architecture

Canonical runtime path:

`StrategyPlugin → TradeIntent → PortfolioAllocationPolicy → PortfolioRisk → ExecutionPlan`

`StrategyRuntime` uses the same plugin `evaluate(context)` semantics for `BACKTEST`, `PAPER`, `SHADOW`, and `LIVE_SEMANTICS`. The runtime has no VenueAdapter or ExecutionCoordinator dependency and therefore cannot place orders directly.

`LIVE_SEMANTICS` is a semantic parity mode, not production authorization.

## PnL / attribution / correlation

Phase 7 adds deterministic analytics contracts for:

- strategy + version PnL attribution;
- fees and funding;
- duplicate-event rejection to prevent double counting;
- pairwise strategy-return correlation on overlapping periods only.

Canonical Ledger remains the eventual evidence source; Phase 7 analytics consume canonical attribution observations and do not create an alternative execution ledger.
