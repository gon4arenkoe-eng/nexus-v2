# AIEA Research Sandbox CI Runtime Certification v1

## Purpose

Prove the runtime isolation contract for AI-generated AIEA research code on a dev/research CI host. This workflow is evidence-only. It does not deploy, publish images, write packages, access exchange credentials, or change production authority.

## Trigger before main closure

Create a temporary branch named `aiea-sandbox-cert/<label>` containing the sandbox candidate and this workflow. A push to that branch runs `.github/workflows/aiea-research-sandbox-certification.yml` on `ubuntu-24.04`.

After the workflow is green, preserve the GitHub Actions run URL and the uploaded evidence artifact. Only then update `NEXUS_PROJECT_AUDIT.md` and close the capability on `main`.

## Runtime image

The workflow uses a Docker Official Python image referenced only by immutable `sha256` digest. No image is built or pushed by this certification workflow.

## Required runtime evidence

The certification script must emit all of:

- `DOCKER_DAEMON=PASS`
- `IMAGE_DIGEST_PIN=PASS`
- `NETWORK_ISOLATION_RUNTIME=PASS`
- `FILESYSTEM_READONLY_RUNTIME=PASS`
- `SECRETS_ISOLATION_RUNTIME=PASS`
- `DOCKER_SOCKET_ISOLATION_RUNTIME=PASS`
- `RESOURCE_LIMIT_COMMAND_CONTRACT=PASS`
- `AIEA_RESEARCH_SANDBOX_RUNTIME_CERTIFIED=PASS`

The workflow uploads an artifact containing:

- runtime certification log;
- Docker image inspect output;
- immutable metadata containing commit/ref/run/image identity;
- `SHA256SUMS.txt` for the evidence files.

## Fail-closed rules

The workflow must remain read-only at GitHub permission level (`contents: read`). It must not use repository secrets, package write permissions, OIDC write permissions, Docker login, Docker build, Docker push, self-hosted production runners, or Docker socket mounts.

## Production safety

This certification does not expand trading authority. AI promotion remains SHADOW-ONLY, advisory remains OBSERVE_ONLY, Restricted Live and Full Live remain DISABLED, and AI direct exchange access remains BLOCKED.
