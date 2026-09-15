# Phase 13 — Bybit V2 Adapter Foundation v1

Scope: adapter/normalization foundation only. Runtime HTTP signing, credentials,
real Demo Trading certification, controlled writes, WebSocket confirmation, and
final venue gate closure are separate slices.

## Environment

- Canonical venue: `BYBIT`
- Target product: V5 `linear` USDT perpetual
- Foundation environment: `DEMO`
- Official Demo Trading REST host for later transport slice: `https://api-demo.bybit.com`
- Production host is not introduced by this foundation.
- Writes are disabled by default.
- Position mode is fail-closed to one-way (`positionIdx=0`).

## Canonical reads

- order/open orders: `/v5/order/realtime`
- positions: `/v5/position/list`
- account: `/v5/account/wallet-balance`
- fills: `/v5/execution/list`

The adapter unwraps Bybit's `retCode/retMsg/result/list` envelope and maps raw
fields only inside `adapters/bybit`.

## Balance semantic decision

Bybit documents per-coin `availableToWithdraw` as deprecated for UNIFIED
accounts. To avoid inventing unsafe per-coin availability, v1 exposes one
account-level USD valuation balance using documented `totalWalletBalance` and
`totalAvailableBalance`. A richer per-coin collateral model is a separate
explicit contract/capability decision, not silently inferred here.

## Writes

`submit_order` and `cancel_order` are present because they are part of the
canonical VenueAdapter surface, but both fail closed unless `allow_demo_writes`
is explicitly enabled. Because Bybit order create/cancel acknowledgements are
asynchronous, the adapter performs a read-back through `/v5/order/realtime`
instead of treating the acknowledgement as final state.

## Not certified by this slice

- real HTTP/HMAC transport;
- Demo Trading credentials/runtime;
- hedge mode;
- pagination completeness;
- private WebSocket gap/replay behavior;
- real controlled write execution;
- `NEXUS_V2_VENUE_BYBIT_CERTIFIED_OK`.
