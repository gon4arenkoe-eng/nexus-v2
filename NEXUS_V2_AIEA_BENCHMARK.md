# NEXUS V2 AIEA — Phase 9 Reference Benchmark

Date: 2026-09-12
Gate: `NEXUS_V2_AIEA_OK`

## Purpose

Phase 9 builds AIEA as an evidence-driven research/evolution bounded context. It does not grant production execution authority. The implementation follows NEXUS-owned contracts and uses mature projects only as architectural references.

## Reference comparison

| Reference | Useful pattern | NEXUS adoption | Runtime/source dependency |
|---|---|---|---|
| Microsoft Qlib | experiment/recorder hierarchy, workflow/data/model lifecycle, online/offline research management | immutable experiment/artifact identities and reproducibility metadata | none |
| Microsoft RD-Agent | hypothesis → experiment/code → execution → feedback → next hypothesis loop | bounded research worker plus closed evidence→hypothesis→candidate→falsification→lesson cycle | none |
| Freqtrade/FreqAI | lookahead analysis, dry/backtest caution, model freshness/expiration | mandatory leakage gate and explicit freshness/drift evidence | none |
| VectorBT | fast parameter/research exploration and dense portfolio analytics | research-acceleration reference only; no embedding | none |
| FinRL / FinRL-X | train/test/trade separation, modular AI research pipeline | strict dataset split identity and off-production experimentation | none |

## License / reuse decision

- Qlib: MIT. Patterns only in Phase 9.
- RD-Agent: MIT. Patterns only; autonomous code execution remains isolated behind a NEXUS port.
- Freqtrade: GPL-3.0. Reference only; no source reuse or runtime dependency.
- VectorBT: Apache 2.0 with Commons Clause. Reference only; embedding requires separate license review.
- FinRL: MIT; FinRL-X / FinRL-Trading: Apache-2.0. Reference only.

No external research framework is introduced as a production runtime dependency by Phase 9.

## Phase 9 decisions

### 1. Persistent research memory

AIEA records immutable, tenant-scoped research evidence in `aiea_research_records` using `(workspace_id, user_id, record_type, record_id)` ownership. Duplicate identical records are idempotent; conflicting immutable content fails closed.

### 2. Falsification-first

Every hypothesis predeclares all mandatory falsification checks:

- lookahead/leakage;
- holdout isolation;
- realistic costs;
- OOS;
- walk-forward;
- regime stability;
- symbol stability;
- parameter stability;
- capacity/liquidity;
- minimum sample;
- tail risk;
- data quality;
- false-discovery control.

Missing evidence is a rejection, not an implicit pass.

### 3. Immutable strategy evolution

A candidate has immutable parent/version, before/after spec hashes, dataset/feature lineage, code hash, environment digest and execution-cost model identity. Production versions are not rewritten in place.

### 4. Evidence-bound promotion

A passing candidate can become `SHADOW_READY` only. Exact dataset/code/environment/evidence hashes and rollback version are bound into the readiness record. Independent risk and permission approval remain mandatory.

### 5. Champion/challenger adaptation

Drift creates explicit `HEALTHY / WATCH / DEGRADED / UNKNOWN` assessments. Degradation can initiate research/challenger work; it never mutates a live champion directly.

### 6. Isolated autonomous R&D

`workers/aiea_research` enforces a bounded sandbox policy:

- finite wall time / memory / CPU;
- dependency allowlist;
- network disabled at the Phase 9 policy boundary;
- no exchange credentials;
- no production filesystem writes;
- forbidden execution/exchange authority tokens.

The worker returns experiment evidence through `ResearchWorkerPort`; it has no `VenueAdapter` or `ExecutionCoordinator` dependency.

## External references

- Qlib Recorder / experiment management: https://github.com/microsoft/qlib/blob/main/docs/component/recorder.rst
- Qlib project: https://github.com/microsoft/qlib
- RD-Agent: https://github.com/microsoft/RD-Agent
- Freqtrade lookahead analysis: https://docs.freqtrade.io/en/latest/lookahead-analysis/
- FreqAI model freshness/expiration: https://docs.freqtrade.io/en/stable/freqai-running/
- VectorBT: https://github.com/polakowo/vectorbt
- FinRL-X / FinRL-Trading: https://github.com/AI4Finance-Foundation/FinRL-Trading

## Safety decision

Phase 9 does not change production permissions:

- AI promotion path: SHADOW-ONLY;
- Advisory: OBSERVE_ONLY;
- Restricted Live: DISABLED;
- Full Live: DISABLED;
- AI direct exchange access: BLOCKED.
