# NEXUS V2 Decision Intelligence / Reasoning Benchmark

**Date:** 2026-09-13
**Status:** architecture approved; foundation implementation test-verified in this changeset

## Purpose

Close the verified gap between canonical `MarketContext`, Phase 7 strategy runtime/allocation and Phase 9 AIEA without creating a second execution owner.

## Adopted pattern

```text
MarketContext
в†’ MarketDecisionSnapshot
в†’ StrategyOpportunityAssessment[]
в†’ StrategyPortfolioDecision / NO_TRADE
в†’ PortfolioRisk
в†’ StrategyRuntime / TradeIntent
в†’ Core Execution
в†’ Ledger
в†’ DecisionOutcome
в†’ DecisionEvaluation
в†’ Decision Memory
в†’ AIEA evidence
```

LLM reasoning is optional and research/advisory only:

```text
Decision Memory / News / Evidence
в†’ ReasoningModelPort
в†’ structured ReasoningArtifact
в†’ AIEA hypothesis / critique
в†’ validation / falsification
в†’ promotion readiness
```

## Reference findings

### QuantConnect LEAN

Useful pattern: Alpha/insight generation, portfolio construction, Risk and execution are separate responsibilities. NEXUS adopts the separation principle, not LEAN source ownership.

Reference: https://github.com/QuantConnect/Lean

### Microsoft Qlib

Useful pattern: predictive signals/scores are distinct from portfolio strategy/construction. NEXUS adopts explicit conversion from opportunity assessments to portfolio recommendations rather than treating a single score as an order.

Reference: https://github.com/microsoft/qlib

### Groq

Groq exposes an OpenAI-compatible API base URL `https://api.groq.com/openai/v1`, supports chat completions and JSON/structured output modes, and currently lists free-plan limits for open-weight GPT-OSS models. NEXUS uses this only behind `ReasoningModelPort`.

References:
- https://console.groq.com/docs/openai
- https://console.groq.com/docs/structured-outputs
- https://console.groq.com/docs/rate-limits
- https://console.groq.com/docs/models

### Ollama

Ollama exposes OpenAI-compatible local endpoints such as `/v1/chat/completions`. NEXUS treats Ollama as a local/offline adapter option; the production server is not required to host a model.

Reference: https://docs.ollama.com/api/openai-compatibility

## Safety invariants

- Decision Intelligence never writes to VenueAdapter or exchange clients.
- Portfolio Risk remains mandatory authority for exposure.
- Core owns execution/recovery/reconciliation/Ledger.
- LLM outage only degrades reasoning/research.
- LLM output is not validation evidence or promotion approval.
- AI-generated strategy/model changes still require AIEA falsification, OOS/WF, shadow and independent promotion/risk/permission gates.
- Credentials remain outside domain contracts.
