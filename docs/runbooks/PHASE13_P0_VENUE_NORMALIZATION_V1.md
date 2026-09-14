# Phase 13 P0 Venue Normalization Foundation v1

## Scope

This slice standardizes the adapter-layer boundary for venue-specific raw API
payload normalization. It does **not** implement Binance, Bybit, or OKX and it
does not expand production/live authority.

P0 certification targets remain BingX, Binance USD-M, Bybit, and OKX.

## Architecture

Raw venue payload -> venue-specific mapper -> canonical VenueAdapter values -> Core.

There is deliberately no universal raw JSON parser. Field names, status values,
position modes, pagination, order flags, and endpoint capabilities vary by venue.
The shared layer therefore standardizes mapper protocols and canonical validation,
while each venue owns its raw payload interpretation.

## BingX reference evidence

BingX already performs raw-to-canonical normalization inside
`adapters/bingx/venue.py` and passes the reusable VenueAdapter reconciliation-read
contract. This slice adds reference tests that also prove a recreated adapter can
re-read the same deterministic raw observations into an identical canonical
snapshot. Restart/recovery authority remains owned by Core persistence and
reconciliation, not by the mapper.

## Future venue implementation sequence

For Binance/Bybit/OKX and later venues:

1. implement the venue transport/auth boundary;
2. implement venue-specific normalization against the shared mapper contracts;
3. expose only canonical VenueAdapter values;
4. run generic adapter/reconciliation contract tests;
5. run venue-specific mapping/edge-case tests;
6. run safe runtime/demo certification where supported;
7. record per-venue evidence and certification status.

## Safety

- raw venue fields never become canonical Core fields;
- no credentials are introduced here;
- no production deployment is performed;
- no live authority is expanded;
- unsupported/unknown venue semantics must fail closed or remain explicit UNKNOWN.
