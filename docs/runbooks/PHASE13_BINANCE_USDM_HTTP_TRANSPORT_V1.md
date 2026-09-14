# Phase 13 — Binance USD-M sandbox HTTP/signing transport v1

Status target: TEST VERIFIED foundation only. This slice does **not** certify a real Binance account or close the Binance venue gate.

## Scope

- HMAC-SHA256 signing of exact URL-encoded request parameters.
- `timestamp` and `recvWindow` owned by the transport.
- `X-MBX-APIKEY` header.
- strict `/fapi/` path boundary.
- sandbox host allowlist only.
- default sandbox host: `https://demo-fapi.binance.com`.
- legacy compatibility host: `https://testnet.binancefuture.com`.
- writes disabled by default and require explicit transport opt-in.
- production host is rejected.
- sanitized HTTP/network/JSON errors; no secret/body echo.

## External endpoint evidence / contradiction

Binance's official signature example repository still demonstrates USD-M testnet with `https://testnet.binancefuture.com`, while current 2026 Binance SDK usage and mature integrations use the renamed/demo USD-M REST host `https://demo-fapi.binance.com`. NEXUS therefore does not silently equate the two environments. The transport defaults to the current demo host, retains the legacy host only as an explicit sandbox allowlist option, and requires real runtime certification before the Binance gate can close.

## Explicitly deferred

- real credentials / real network probe;
- account permission validation;
- clock-skew/server-time correction policy;
- retry/backoff/rate-limit policy certification;
- runtime read-only certification;
- controlled order lifecycle certification;
- hedge mode;
- private WebSocket/user-data stream;
- production/live enablement.

## Safety

This transport cannot target `https://fapi.binance.com`. Writes have a second fail-closed gate independent of the VenueAdapter config. No Core dependency on credentials or raw Binance fields is introduced.
