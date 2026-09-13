# AIEA Research Sandbox / Compute Isolation v1

Phase 9 boundary for AI-generated research code. This is an **off-production** worker runtime; production receives only approved versioned artifacts.

## Runtime contract

Generated Python is validated before launch, must define `run(input_data)`, and is executed through a digest-pinned Docker image. The container command is fail-closed and includes:

- `--network none`;
- `--read-only` root filesystem plus a bounded `/tmp` tmpfs;
- no bind mounts / volumes and therefore no Docker socket mount;
- `--cap-drop ALL` and `no-new-privileges`;
- non-root uid/gid;
- memory, CPU, PID and file-descriptor limits;
- immutable image digest and `--pull never`;
- wall-clock timeout enforced by the host executor;
- source/input passed only over stdin;
- no production secrets or exchange credentials supplied to the container.

Static AST validation additionally rejects imports outside the policy allowlist and dangerous filesystem/network/process/dynamic-code operations. This is defense in depth; the Docker boundary remains authoritative for runtime isolation.

## Runtime certification

Unit tests prove command construction and fail-closed behavior. They are not a substitute for a real Docker-host security check. On a **dev/research host**, first make a reviewed Python sandbox image available locally and resolve it to an immutable digest, then run:

```powershell
.\.venv\Scripts\python.exe scripts\aiea_research_sandbox_certify.py "ghcr.io/.../aiea-research-sandbox@sha256:<digest>"
```

Certification must report runtime PASS for network isolation, read-only filesystem, host-secret absence and Docker-socket absence. Do not run builds, ML sweeps or this certification on production `nexus-bot`.

## Production safety

This boundary does not grant candidate promotion or live execution authority. No `VenueAdapter` write, `ExecutionCoordinator`, credentials, production DB, or Docker socket is exposed to generated code. AI promotion remains SHADOW-only until later gates explicitly change that policy.
