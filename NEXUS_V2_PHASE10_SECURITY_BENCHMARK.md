# NEXUS V2 Phase 10 — Multi-user / Settings / Security benchmark

## Scope

Phase 10 establishes the backend foundation for workspace/tenant ownership,
RBAC, hierarchical settings, secret isolation, generic audit evidence,
subscriptions/entitlements/quotas and tenant-scoped jobs/events.

## Reference patterns

- **OpenFGA** — mature relationship/role authorization model. NEXUS adopts
  workspace-scoped authorization decisions and explicit resource ownership;
  no OpenFGA runtime dependency is added in Phase 10.
- **Apache Casbin** — mature RBAC-with-domains/tenants reference. NEXUS keeps a
  small explicit OWNER / ADMIN / TRADER / VIEWER matrix in owned contracts.
- **OWASP Logging Cheat Sheet** — tokens, passwords, connection strings and
  encryption keys must not be logged. NEXUS secret contracts redact ciphertext
  from repr and keep AIEA workers outside the credential-access boundary.

## NEXUS-specific invariants

1. Every authorization decision is workspace scoped.
2. Cross-tenant resource ownership fails closed even for privileged roles.
3. Role permission, entitlement, quota and trading safety are separate checks.
4. Payment/subscription state can block new premium actions but cannot disable
   cancel/close/reduce/reconciliation/protection/recovery paths.
5. Settings resolution order is system → workspace → account → risk profile →
   strategy instance → session override.
6. Safety-critical setting changes require actor, old/new value, timestamp and
   reason in immutable audit evidence.
7. Product plans use immutable plan versions and stable FeatureKey values.
8. Billing events are idempotent immutable evidence.
9. Quota reservation uses an atomic conditional UPDATE against an existing
   workspace/quota/period row.
10. Secrets are stored only as encrypted envelopes with key-version metadata;
    plaintext is not stored by Phase 10 persistence.
11. AIEA workers cannot access the secret boundary.
12. Background-job and realtime-event scopes carry workspace and user ownership.

## Dependency policy

- No FastAPI, exchange client, VenueAdapter or ExecutionCoordinator dependency
  is introduced into Phase 10 contracts/application logic.
- No billing-provider SDK enters Core domain/application logic.
- No new live authority is granted.
