# NEXUS V2 backup / restore foundation

## Scope

This Phase 12 runbook defines evidence requirements for a pre-cutover backup and an isolated restore rehearsal. It does not claim that the required Phase 15 production backup/restore drill has been completed.

## Backup evidence

Before a future controlled cutover, create a PostgreSQL backup using an approved operator environment. Never print database credentials into logs.

Reference command shape:

```bash
pg_dump --format=custom --file=<backup-file> <database-connection>
```

Record at minimum:

- UTC timestamp;
- source environment/DB identity without secrets;
- source Git commit;
- candidate image digest;
- current Alembic head;
- backup artifact reference;
- backup artifact SHA-256 checksum;
- operator/audit reference.

The backup artifact must be stored outside the application container/runtime filesystem according to the approved retention policy.

## Verification

1. Confirm the backup artifact exists and is non-empty.
2. Compute and record its SHA-256 checksum.
3. Keep the checksum with the release evidence record.
4. Perform an **isolated restore rehearsal** into a disposable/non-production database using `pg_restore` before relying on the artifact.
5. Verify schema/migration state and representative canonical records after the rehearsal.

Example rehearsal shape:

```bash
pg_restore --clean --if-exists --no-owner --dbname=<isolated-rehearsal-db> <backup-file>
```

## Production restore boundary

A production restore is destructive/high-impact and is not automatically authorized by this runbook. The required production backup/restore drill belongs to Phase 15 Cutover Readiness and must have explicit evidence and authorization.

If deployment/rollback can be completed safely without a database restore, prefer the immutable image rollback path. Never perform a destructive production restore as an automatic reconciliation action.
