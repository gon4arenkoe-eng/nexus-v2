# Phase 13 — Bybit V5 Demo HTTP Transport v1

Status target: foundation transport only. This slice does **not** close `NEXUS_V2_VENUE_BYBIT_CERTIFIED_OK`.

## Scope

- Demo Trading REST host only: `https://api-demo.bybit.com`.
- V5 HMAC-SHA256 authentication headers.
- GET signing over exact canonical query string.
- POST signing over exact canonical JSON body.
- Writes disabled by default at transport level.
- Sanitized HTTP/network error evidence.
- No retry loop and no runtime credentials in repository.

The existing `BybitVenueAdapter` remains a separate adapter boundary and still owns canonical normalization. Raw Bybit payloads do not enter Core.

## Explicitly not included

- live/production Bybit transport;
- Bybit Testnet transport;
- real credentials;
- runtime network certification;
- retry/backoff policy;
- WebSocket transport;
- hedge mode;
- final venue certification gate closure.

## Verification

Use Python 3.13. Type-check with `--explicit-package-bases` because the repository uses namespace packages. Run pytest from the repository `.venv`, which contains the declared test dependencies including `pytest-asyncio`.

Expected safety invariants:

- production `api.bybit.com` literal absent from transport source;
- testnet `api-testnet.bybit.com` literal absent from transport source;
- `allow_demo_writes=False` by default;
- non-GET request fails before network unless explicitly enabled;
- credentials/signatures are not rendered in sanitized HTTP evidence;
- `NEXUS_V2_VENUE_BYBIT_CERTIFIED_OK` remains OPEN.
