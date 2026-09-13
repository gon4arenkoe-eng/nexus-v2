# BingX DEMO Certification Runbook

## Safety state

- Environment: DEMO/VST only.
- Restricted Live: DISABLED.
- Full Live: DISABLED.
- AI direct exchange access: BLOCKED.
- Adapter writes: disabled by default; explicit DEMO enablement required.

## Deterministic certification matrix

1. Canonical order normalization.
2. Open-order discovery.
3. LONG/SHORT hedge position identity.
4. VST account balance observation.
5. Immutable fill normalization.
6. Missing/unknown client order identity fallback.
7. UNKNOWN order state remains explicit.
8. Rate-limit/system-busy failures remain explicit and retryable only at the
   transport/runtime policy layer.
9. Generic VenueAdapter read contract passes.
10. Wrong venue/account identity fails before transport I/O.

## Live DEMO gate (not performed by this delivery)

A later authorized certification run must use credential-safe transport against
BingX VST and record:

- account read;
- positions read;
- open-orders read;
- fill-history read;
- one minimal-size DEMO submit/ack/query/cancel lifecycle;
- one minimal-size DEMO fill lifecycle if explicitly approved;
- restart/reconciliation observations after the lifecycle;
- rate-limit/unavailable handling evidence without destructive correction.

The live DEMO run is evidence only. It must not expand production trading
authority.
