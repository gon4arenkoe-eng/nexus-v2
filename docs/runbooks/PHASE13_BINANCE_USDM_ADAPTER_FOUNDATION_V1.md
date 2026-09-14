# Phase 13 — Binance USD-M VenueAdapter Foundation v1

Status target: TEST VERIFIED FOUNDATION only. This is not venue certification.

## Scope

- Binance USD-M canonical `VenueAdapter` implementation over an injected transport.
- Venue-specific raw payload normalization for orders, positions, balances and fills.
- Reuse of the Phase-13 shared venue normalization contract and generic read-contract testkit.
- TESTNET-only configuration.
- Writes disabled by default; opt-in write mapping tested only through fake transport.
- ONEWAY position mode only in this slice. HEDGE mode is fail-closed and requires a separate canonical position-mode design/implementation step.

## Explicitly out of scope

- real HTTP/signing transport;
- API credentials;
- live/production endpoint;
- user data WebSocket;
- HEDGE mode writes;
- leverage/margin-mode mutation;
- runtime testnet certification;
- `NEXUS_V2_VENUE_BINANCE_CERTIFIED_OK` closure.

## Safety

Raw Binance payload fields remain in `adapters/binance`. Core receives canonical values only. No production authority is expanded.
