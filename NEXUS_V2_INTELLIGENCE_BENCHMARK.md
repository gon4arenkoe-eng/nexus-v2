# NEXUS V2 Intelligence Benchmark

## Scope

Phase 8 implements the canonical read-only Intelligence boundary required by
`NEXUS_V2_MASTER_PLAN.md`:

- canonical market observations;
- event-time and ingestion-time tracking;
- provenance/schema identity;
- freshness, gap, duplicate and outlier quality evidence;
- candles/trades/top-of-book/order-book depth;
- funding/open-interest and mark/index context;
- news/event risk;
- cross-market correlation observations;
- deterministic MarketContext construction;
- explicit CURRENT/STALE/DEGRADED/UNAVAILABLE/UNKNOWN quality states;
- no order execution authority.

## Reference comparison

### NautilusTrader

Reference pattern: market data objects separate venue event time from local
initialization time. NEXUS adopts the same conceptual separation as
`event_time` versus `ingestion_time`, while retaining NEXUS-owned contracts.

Reference:
https://nautilustrader.io/docs/latest/concepts/data/

### Hummingbot

Reference pattern: market-data services expose candles, prices, order-book
state and funding information separately from executor/order-management
responsibilities. NEXUS adopts the separation of market observation from
execution authority.

References:
https://hummingbot.org/hummingbot-api/routers/
https://hummingbot.org/strategies/v2-strategies/data/

### Microsoft Qlib

Reference pattern: normalized instruments, calendars and feature retrieval are
owned by a data layer rather than by trading execution. NEXUS adopts the
normalized-data boundary but does not add Qlib as a runtime dependency.

Reference:
https://github.com/microsoft/qlib/blob/main/docs/start/getdata.rst

## NEXUS decision

Phase 8 is deliberately a canonical read-only bounded context under
`apps/intelligence`. Venue-specific response normalization must happen before
these contracts. Strategies, Portfolio Risk and AIEA may consume
`MarketContext`; Intelligence may not submit/cancel orders or access execution
credentials.

No external reference implementation is copied and no new runtime dependency
is introduced by Phase 8.
