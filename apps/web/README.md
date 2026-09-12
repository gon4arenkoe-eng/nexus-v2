# NEXUS V2 Control Plane

Phase 11 typed frontend shell. It is presentation-only and has no database,
venue-client, credential or order-execution dependency.

## Local preview

```bash
cd apps/web
python -m http.server 8080
```

Open `http://localhost:8080`.

## Type check / build

```bash
tsc --noEmit
tsc
```

Compiled ES modules are committed under `compiled/` for deterministic review.

The source intentionally uses native TypeScript + DOM/CSS Grid to keep the
Phase 11 supply chain minimal. Canonical workspace ownership and persistence
remain backend-authoritative.
