# NEXUS V2 Multi-Market Extensibility v1

Status: approved architecture foundation; non-crypto venue integrations are deferred until a post-launch update.

## Launch vs future scope

Current launch/cutover scope remains the approved crypto venue program. This change does not add live authority, production credentials, or new non-crypto adapters.

Future updates may add equities/ETFs, FX, futures, options, CFDs and multi-asset brokers through canonical contracts and per-venue certification.

## Invariants

- `InstrumentId` remains the stable execution identity.
- Market-specific properties live in optional canonical `InstrumentDefinition` contracts.
- Core must not infer instrument semantics by parsing native venue symbols.
- Unsupported capabilities fail closed.
- Funding, corporate actions, expiry/exercise, sessions, settlement and margin are optional declared capabilities, not universal assumptions.
- Adapters translate raw venue/broker payloads into canonical contracts.
- New asset classes/venues require their own adapter tests and certification evidence.
- Future-ready does not mean implemented, certified or live-enabled.

## Post-launch integration shape

`new venue/market -> adapter -> capabilities -> instrument definitions -> canonical execution/reconciliation -> tests -> venue certification`

No direct broker/exchange payload is permitted in canonical Core.
