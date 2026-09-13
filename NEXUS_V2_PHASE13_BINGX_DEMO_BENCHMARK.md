# NEXUS V2 Phase 13 — BingX DEMO Adapter Benchmark

## Scope

This slice implements the first concrete V2 venue adapter for BingX perpetual
swap DEMO/VST and validates it against the existing canonical VenueAdapter read
contract suite.

## Source facts retained from legacy

Legacy `clients/bingx.py` was used only as a behavior reference. Retained facts:

- BingX perpetual symbols are represented externally as `BTC-USDT` style names;
- hedge mode exposes `positionSide` and LONG/SHORT must remain distinct;
- positions expose `positionAmt` plus average/entry price;
- DEMO uses VST and must not silently become production USDT authority;
- legacy had order/open-order/position/balance primitives.

Direct legacy mutations, execution authority, credentials and raw response
objects are not copied into Core.

## GitHub-first / current BingX API research

Current BingX API references checked on 2026-09-12:

- BingX-API/api-ai-skills — swap-trade API reference;
- BingX-API/api-ai-skills — swap-account reference.

Relevant current endpoints:

- POST/DELETE/GET `/openApi/swap/v2/trade/order`;
- GET `/openApi/swap/v2/trade/openOrders`;
- GET `/openApi/swap/v2/trade/fillHistory`;
- GET `/openApi/swap/v2/user/positions`;
- GET `/openApi/swap/v3/user/balance`;
- BingX VST base URL is documented separately from live production.

Current order status vocabulary includes NEW, PARTIALLY_FILLED, FILLED,
CANCELED and EXPIRED. Rate-limit error 100410 and transient system busy codes
are kept explicit at the adapter boundary.

## Architecture decision

`BingXVenueAdapter` lives under `adapters/bingx` and depends on an injected
`BingXTransport` Protocol. Transport owns authentication, credentials, HTTP and
retry timing. The adapter owns normalization only.

This preserves the forbidden-dependency rules:

- Core does not import BingX clients or raw payloads;
- raw fields remain under the BingX adapter boundary;
- strategy/AIEA have no venue write access;
- no production credential or deploy authority is introduced.

## DEMO write safety

Phase 13 adapter config is DEMO-only. `environment=REAL` fails closed. DEMO
writes are also disabled by default and require explicit
`allow_demo_writes=True` at composition time.

This does **not** enable Restricted Live or Full Live.

## Certification status of this slice

This delivery proves deterministic adapter normalization and the shared contract
suite with scripted transport evidence. It does not claim live network DEMO
certification yet. A subsequent Phase 13 step must bind a credential-safe BingX
VST transport and run the approved live DEMO certification matrix before
`NEXUS_V2_VENUE_BINGX_CERTIFIED_OK` may close.
